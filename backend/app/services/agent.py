"""Agent service with tools for email response generation."""

from typing import Dict, Any, List, Optional
import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.listing import Listing, ListingDocumentChunk
from app.models.lead import NDA, NDAStatus
from app.models.broker import BrokerSettings
from app.services.openai_service import OpenAIService
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class AgentTools:
    """Tools available to the LLM agent."""

    def __init__(self, db: AsyncSession):
        """Initialize tools with database session."""
        self.db = db

    async def identify_listing(self, email_text: str, broker_id: str) -> Dict[str, Any]:
        """
        Identify listing from email text by matching code or title.

        Args:
            email_text: Email content
            broker_id: Broker UUID

        Returns:
            Dict with listing_id and confidence
        """
        logger.info(
            "Agent tool called: identify_listing",
            extra={"broker_id": broker_id, "email_length": len(email_text)}
        )

        # Search for listings that match keywords in email
        result = await self.db.execute(
            select(Listing).where(
                Listing.broker_id == broker_id,
                Listing.status == "active",
            )
        )
        listings = result.scalars().all()

        # Simple keyword matching (can be improved with NLP)
        best_match = None
        best_score = 0

        for listing in listings:
            score = 0

            # Check if code is mentioned
            if listing.code.lower() in email_text.lower():
                score += 10

            # Check if title words are mentioned
            title_words = listing.title.lower().split()
            for word in title_words:
                if len(word) > 3 and word in email_text.lower():
                    score += 2

            if score > best_score:
                best_score = score
                best_match = listing

        if best_match and best_score >= 5:
            logger.info(
                "Listing identified",
                extra={
                    "listing_id": str(best_match.id),
                    "listing_code": best_match.code,
                    "confidence": min(best_score / 20.0, 1.0),
                }
            )
            return {
                "listing_id": str(best_match.id),
                "listing_code": best_match.code,
                "listing_title": best_match.title,
                "confidence": min(best_score / 20.0, 1.0),
            }

        logger.warning("No listing identified from email text", extra={"broker_id": broker_id})
        return {"listing_id": None, "confidence": 0.0}

    async def get_listing_summary(self, listing_id: str) -> Dict[str, Any]:
        """
        Get public listing summary (non-sensitive info).

        Args:
            listing_id: Listing UUID

        Returns:
            Dict with listing details
        """
        result = await self.db.execute(
            select(Listing).where(Listing.id == listing_id)
        )
        listing = result.scalar_one_or_none()

        if not listing:
            return {"error": "Listing not found"}

        return {
            "code": listing.code,
            "title": listing.title,
            "asking_price": float(listing.asking_price) if listing.asking_price else None,
            "location_region": listing.location_region,
            "short_description": listing.short_description,
            "status": listing.status.value,
        }

    async def search_listing_knowledge(
        self, listing_id: str, query: str, limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Search listing documents using vector similarity (RAG).

        Args:
            listing_id: Listing UUID
            query: Search query
            limit: Number of results (default 3)

        Returns:
            List of relevant chunks with content, metadata, and distance
        """
        from app.models.listing import ListingDocument, ListingDocumentChunk
        from sqlalchemy import text

        # Generate query embedding
        openai_service = OpenAIService()
        query_embedding = openai_service.create_embedding(query)

        if not query_embedding:
            return []

        # Convert embedding to pgvector format
        # pgvector expects format: '[0.1,0.2,0.3,...]'
        embedding_str = '[' + ','.join(str(x) for x in query_embedding) + ']'

        # Perform vector similarity search using pgvector's <-> operator (cosine distance)
        # Lower distance = more similar
        query_sql = text("""
            SELECT
                c.id,
                c.content,
                c.metadata,
                c.page_number,
                d.document_type,
                d.title,
                (c.embedding <-> :query_embedding::vector) as distance
            FROM listing_document_chunks c
            JOIN listing_documents d ON c.listing_document_id = d.id
            WHERE d.listing_id = :listing_id
            ORDER BY distance ASC
            LIMIT :limit
        """)

        result = await self.db.execute(
            query_sql,
            {
                "query_embedding": embedding_str,
                "listing_id": str(listing_id),
                "limit": limit,
            }
        )

        rows = result.fetchall()

        # Format results
        chunks = []
        for row in rows:
            chunks.append({
                "chunk_id": str(row.id),
                "content": row.content,
                "metadata": row.metadata or {},
                "page_number": row.page_number,
                "document_type": row.document_type,
                "document_title": row.title,
                "distance": float(row.distance),
                "similarity": 1 - float(row.distance),  # Convert distance to similarity (0-1)
            })

        return chunks

    async def get_nda_status(self, lead_id: str, listing_id: str) -> Dict[str, Any]:
        """
        Check NDA status for a lead and listing.

        Args:
            lead_id: Lead UUID
            listing_id: Listing UUID

        Returns:
            Dict with NDA status
        """
        result = await self.db.execute(
            select(NDA).where(
                NDA.lead_id == lead_id,
                NDA.listing_id == listing_id,
            )
        )
        nda = result.scalar_one_or_none()

        if not nda:
            return {"status": "none", "signed": False}

        return {
            "status": nda.status.value,
            "signed": nda.status == NDAStatus.SIGNED,
            "signed_at": nda.signed_at.isoformat() if nda.signed_at else None,
        }

    async def generate_nda_link(
        self, lead_id: str, listing_id: str, broker_id: str
    ) -> str:
        """
        Generate NDA link for lead.

        Args:
            lead_id: Lead UUID
            listing_id: Listing UUID
            broker_id: Broker UUID

        Returns:
            NDA URL
        """
        # Get broker settings for default NDA URL
        result = await self.db.execute(
            select(BrokerSettings).where(BrokerSettings.broker_id == broker_id)
        )
        settings = result.scalar_one_or_none()

        if not settings or not settings.default_nda_url:
            return "Please contact us for NDA details"

        # Append query params for tracking
        nda_url = settings.default_nda_url
        nda_url += f"?lead_id={lead_id}&listing_id={listing_id}"

        return nda_url

    async def get_broker_settings(self, broker_id: str) -> Dict[str, Any]:
        """
        Get broker settings (calendly link, etc.).

        Args:
            broker_id: Broker UUID

        Returns:
            Dict with settings
        """
        result = await self.db.execute(
            select(BrokerSettings).where(BrokerSettings.broker_id == broker_id)
        )
        settings = result.scalar_one_or_none()

        if not settings:
            return {}

        return {
            "calendly_link": settings.calendly_link,
            "auto_send_enabled": settings.auto_send_enabled,
        }


class AgentService:
    """Agent orchestration service."""

    def __init__(self, db: AsyncSession):
        """Initialize agent with database and services."""
        self.db = db
        self.openai_service = OpenAIService()
        self.tools = AgentTools(db)

    def get_system_prompt(self) -> str:
        """
        Get the system prompt for the agent.

        Returns:
            System prompt string
        """
        return """You are an AI assistant helping a business broker respond to email inquiries about business listings.

Your role:
- Answer questions about listings using available data
- Gate sensitive information behind NDA requirements
- Encourage high-intent leads to book meetings
- Escalate uncertain or complex questions to the broker

Guidelines:
1. Be professional, friendly, and concise
2. NEVER make up information - only use data from tools
3. For confidential details (full financials, exact address, customer lists):
   - Check NDA status first
   - If no signed NDA, politely request one and provide link
4. For high-intent leads (serious questions, financial capability), include Calendly booking link
5. If uncertain or question is legal/tax-related, escalate to broker
6. Keep responses under 200 words

Available tools:
- identify_listing: Find which listing an email is about
- get_listing_summary: Get basic public listing info
- search_listing_knowledge: Search uploaded listing documents
- get_nda_status: Check if lead has signed NDA
- generate_nda_link: Get NDA URL for lead
- get_broker_settings: Get broker's Calendly link

When to escalate:
- Question not answerable with available data
- Legal, tax, or financial advice requests
- Angry or complaint emails
- Ambiguous listing identification
- Confidence < 70%
"""

    def create_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Create OpenAI function definitions for tools.

        Returns:
            List of tool definitions
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "identify_listing",
                    "description": "Identify which listing the email is about by matching listing code or title",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "email_text": {
                                "type": "string",
                                "description": "The email text to search for listing references",
                            }
                        },
                        "required": ["email_text"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_listing_summary",
                    "description": "Get public summary of a listing (price, location, description)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "listing_id": {
                                "type": "string",
                                "description": "UUID of the listing",
                            }
                        },
                        "required": ["listing_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_nda_status",
                    "description": "Check if a lead has signed an NDA for a listing",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lead_id": {"type": "string", "description": "UUID of the lead"},
                            "listing_id": {"type": "string", "description": "UUID of the listing"},
                        },
                        "required": ["lead_id", "listing_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_nda_link",
                    "description": "Generate NDA link for a lead",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lead_id": {"type": "string"},
                            "listing_id": {"type": "string"},
                            "broker_id": {"type": "string"},
                        },
                        "required": ["lead_id", "listing_id", "broker_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_broker_settings",
                    "description": "Get broker settings including Calendly link",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "broker_id": {"type": "string", "description": "UUID of the broker"}
                        },
                        "required": ["broker_id"],
                    },
                },
            },
        ]

    async def execute_tool(
        self, tool_name: str, arguments: Dict[str, Any], broker_id: str
    ) -> Any:
        """
        Execute a tool by name.

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            broker_id: Broker UUID

        Returns:
            Tool result
        """
        if tool_name == "identify_listing":
            return await self.tools.identify_listing(
                arguments["email_text"], broker_id
            )

        elif tool_name == "get_listing_summary":
            return await self.tools.get_listing_summary(arguments["listing_id"])

        elif tool_name == "search_listing_knowledge":
            return await self.tools.search_listing_knowledge(
                arguments["listing_id"], arguments["query"]
            )

        elif tool_name == "get_nda_status":
            return await self.tools.get_nda_status(
                arguments["lead_id"], arguments["listing_id"]
            )

        elif tool_name == "generate_nda_link":
            return await self.tools.generate_nda_link(
                arguments["lead_id"], arguments["listing_id"], arguments["broker_id"]
            )

        elif tool_name == "get_broker_settings":
            return await self.tools.get_broker_settings(arguments["broker_id"])

        else:
            return {"error": f"Unknown tool: {tool_name}"}

    async def generate_response(
        self,
        conversation_history: List[Dict[str, str]],
        broker_id: str,
        lead_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a response to an email using the LLM agent.

        Args:
            conversation_history: List of messages in conversation
            broker_id: Broker UUID
            lead_id: Optional lead UUID

        Returns:
            Dict with response text, tool calls, confidence, action
        """
        # Build messages
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            *conversation_history,
        ]

        # Get tool definitions
        tools = self.create_tool_definitions()

        # Call LLM
        response = self.openai_service.chat_completion(
            messages=messages,
            tools=tools,
            temperature=0.7,
        )

        tools_called = []

        # Execute tools if any
        if response.get("tool_calls"):
            for tool_call in response["tool_calls"]:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                # Execute tool
                tool_result = await self.execute_tool(tool_name, tool_args, broker_id)

                tools_called.append({
                    "name": tool_name,
                    "arguments": tool_args,
                    "result": tool_result,
                })

                # Add tool result to messages and call LLM again
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [tool_call],
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result),
                })

            # Get final response after tool execution
            response = self.openai_service.chat_completion(
                messages=messages,
                temperature=0.7,
            )

        # Determine final action and confidence
        final_action = "answer"  # Default
        confidence = 0.8  # Default base confidence

        response_text = response.get("content", "")

        # Track confidence factors
        confidence_factors_positive = []
        confidence_factors_negative = []
        concerns = []
        why_flagged = ""

        # Analyze tools called for confidence factors
        if tools_called:
            for tool in tools_called:
                if tool["name"] == "identify_listing":
                    result = tool.get("result", {})
                    if result.get("confidence", 0) >= 0.7:
                        confidence_factors_positive.append({
                            "factor": "Listing confidently identified",
                            "weight": 0.3
                        })
                    else:
                        confidence_factors_negative.append({
                            "factor": "Listing identification uncertain",
                            "weight": -0.3
                        })
                        concerns.append("Ambiguous listing identification")

                elif tool["name"] == "get_nda_status":
                    result = tool.get("result", {})
                    if result.get("has_nda"):
                        confidence_factors_positive.append({
                            "factor": "NDA verified",
                            "weight": 0.2
                        })
                    else:
                        confidence_factors_negative.append({
                            "factor": "No NDA signed",
                            "weight": -0.2
                        })

                elif tool["name"] == "search_listing_knowledge":
                    result = tool.get("result", {})
                    if result.get("chunks"):
                        confidence_factors_positive.append({
                            "factor": "Relevant documentation found",
                            "weight": 0.2
                        })
                    else:
                        confidence_factors_negative.append({
                            "factor": "No relevant documentation found",
                            "weight": -0.2
                        })
                        concerns.append("Insufficient listing documentation")
        else:
            # No tools called might indicate simple query
            confidence_factors_positive.append({
                "factor": "Standard inquiry pattern",
                "weight": 0.1
            })

        # Simple heuristics for action determination
        if "escalate" in response_text.lower() or "forward" in response_text.lower():
            final_action = "escalate"
            confidence = 0.3
            why_flagged = "Agent determined escalation necessary"
            concerns.append("Question requires broker expertise")

        elif "uncertain" in response_text.lower() or "not sure" in response_text.lower():
            final_action = "escalate"
            confidence = 0.4
            why_flagged = "Agent expressed uncertainty in response"
            concerns.append("Agent lacks confidence in answer")

        elif "nda" in response_text.lower():
            final_action = "ask_nda"
            # Check if actually requesting NDA or just mentioning
            if "sign" in response_text.lower() or "confidential" in response_text.lower():
                confidence_factors_positive.append({
                    "factor": "Appropriate NDA request",
                    "weight": 0.1
                })

        elif "meeting" in response_text.lower() or "call" in response_text.lower():
            final_action = "book_meeting"

        # Calculate final confidence from factors
        positive_weight = sum(f["weight"] for f in confidence_factors_positive)
        negative_weight = sum(f["weight"] for f in confidence_factors_negative)
        confidence = max(0.0, min(1.0, confidence + positive_weight + negative_weight))

        # If confidence is low, escalate
        if confidence < 0.5 and final_action == "answer":
            final_action = "escalate"
            why_flagged = f"Low confidence score ({confidence:.2f})"
            concerns.append("Confidence below acceptable threshold")

        # Build reasoning object
        reasoning = {
            "why_flagged": why_flagged if final_action == "escalate" else "",
            "confidence_factors": {
                "positive": confidence_factors_positive,
                "negative": confidence_factors_negative,
            },
            "concerns": concerns,
            "edge_cases": [],  # Can be populated with specific edge case detection
            "token_usage": response.get("usage", {}),
            "cost_usd": self._calculate_cost(response.get("usage", {})),
        }

        return {
            "response_text": response_text,
            "tools_called": tools_called,
            "confidence": confidence,
            "final_action": final_action,
            "reasoning": reasoning,
            "usage": response.get("usage", {}),
        }

    def _calculate_cost(self, usage: Dict[str, Any]) -> float:
        """
        Calculate approximate cost in USD for this API call.

        GPT-4 pricing (as of Jan 2024):
        - Input: $0.03 per 1K tokens
        - Output: $0.06 per 1K tokens

        Args:
            usage: Token usage dict from OpenAI

        Returns:
            Cost in USD
        """
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)

        # Pricing per 1K tokens
        input_cost_per_1k = 0.03
        output_cost_per_1k = 0.06

        cost = (prompt_tokens / 1000 * input_cost_per_1k) + (completion_tokens / 1000 * output_cost_per_1k)

        return round(cost, 4)
