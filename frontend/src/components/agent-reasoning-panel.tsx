'use client'

import { AgentReasoningDetail } from '@/types'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { AlertTriangle, CheckCircle2, XCircle, Lightbulb } from 'lucide-react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'

interface AgentReasoningPanelProps {
  reasoning: AgentReasoningDetail
  className?: string
}

export function AgentReasoningPanel({
  reasoning,
  className,
}: AgentReasoningPanelProps) {
  const confidenceColor =
    reasoning.confidence >= 0.7
      ? 'success'
      : reasoning.confidence >= 0.5
      ? 'warning'
      : 'destructive'

  const confidenceLabel =
    reasoning.confidence >= 0.7
      ? 'High Confidence'
      : reasoning.confidence >= 0.5
      ? 'Medium Confidence'
      : 'Low Confidence'

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Agent Reasoning</span>
          <Badge variant={confidenceColor}>
            {confidenceLabel} ({(reasoning.confidence * 100).toFixed(0)}%)
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Accordion type="multiple" className="w-full">
          {/* Why Flagged */}
          {reasoning.why_flagged && (
            <AccordionItem value="why-flagged">
              <AccordionTrigger>
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-yellow-600" />
                  <span>Why Flagged for Review</span>
                </div>
              </AccordionTrigger>
              <AccordionContent>
                <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
                  <p className="text-sm text-yellow-900">{reasoning.why_flagged}</p>
                </div>
              </AccordionContent>
            </AccordionItem>
          )}

          {/* Confidence Breakdown */}
          {reasoning.confidence_factors && (
            <AccordionItem value="confidence-factors">
              <AccordionTrigger>
                <div className="flex items-center gap-2">
                  <Lightbulb className="h-4 w-4 text-blue-600" />
                  <span>Confidence Breakdown</span>
                </div>
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-4">
                  {/* Positive Factors */}
                  {reasoning.confidence_factors.positive &&
                    reasoning.confidence_factors.positive.length > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold text-green-700 mb-2 flex items-center gap-1">
                          <CheckCircle2 className="h-4 w-4" />
                          Positive Factors
                        </h4>
                        <ul className="space-y-1">
                          {reasoning.confidence_factors.positive.map(
                            (factor, idx) => (
                              <li
                                key={idx}
                                className="text-sm flex items-center justify-between bg-green-50 px-3 py-2 rounded"
                              >
                                <span>{factor.factor}</span>
                                <Badge variant="success">
                                  +{(factor.weight * 100).toFixed(0)}%
                                </Badge>
                              </li>
                            )
                          )}
                        </ul>
                      </div>
                    )}

                  {/* Negative Factors */}
                  {reasoning.confidence_factors.negative &&
                    reasoning.confidence_factors.negative.length > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold text-red-700 mb-2 flex items-center gap-1">
                          <XCircle className="h-4 w-4" />
                          Negative Factors
                        </h4>
                        <ul className="space-y-1">
                          {reasoning.confidence_factors.negative.map(
                            (factor, idx) => (
                              <li
                                key={idx}
                                className="text-sm flex items-center justify-between bg-red-50 px-3 py-2 rounded"
                              >
                                <span>{factor.factor}</span>
                                <Badge variant="destructive">
                                  {(factor.weight * 100).toFixed(0)}%
                                </Badge>
                              </li>
                            )
                          )}
                        </ul>
                      </div>
                    )}
                </div>
              </AccordionContent>
            </AccordionItem>
          )}

          {/* Concerns */}
          {reasoning.concerns && reasoning.concerns.length > 0 && (
            <AccordionItem value="concerns">
              <AccordionTrigger>
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-orange-600" />
                  <span>Concerns ({reasoning.concerns.length})</span>
                </div>
              </AccordionTrigger>
              <AccordionContent>
                <ul className="space-y-2">
                  {reasoning.concerns.map((concern, idx) => (
                    <li
                      key={idx}
                      className="text-sm bg-orange-50 border border-orange-200 px-3 py-2 rounded"
                    >
                      {concern}
                    </li>
                  ))}
                </ul>
              </AccordionContent>
            </AccordionItem>
          )}

          {/* Tools Called */}
          {reasoning.tools_called && reasoning.tools_called.length > 0 && (
            <AccordionItem value="tools-called">
              <AccordionTrigger>
                <div className="flex items-center gap-2">
                  <span>Tools Called ({reasoning.tools_called.length})</span>
                </div>
              </AccordionTrigger>
              <AccordionContent>
                <div className="flex flex-wrap gap-2">
                  {reasoning.tools_called.map((tool, idx) => (
                    <Badge key={idx} variant="secondary">
                      {tool}
                    </Badge>
                  ))}
                </div>
              </AccordionContent>
            </AccordionItem>
          )}
        </Accordion>

        {/* Confidence Progress Bar */}
        <div className="mt-6">
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="font-medium">Overall Confidence</span>
            <span>{(reasoning.confidence * 100).toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div
              className={`h-full transition-all ${
                reasoning.confidence >= 0.7
                  ? 'bg-green-500'
                  : reasoning.confidence >= 0.5
                  ? 'bg-yellow-500'
                  : 'bg-red-500'
              }`}
              style={{ width: `${reasoning.confidence * 100}%` }}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
