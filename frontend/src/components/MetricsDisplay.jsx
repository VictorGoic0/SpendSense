import { Card, CardHeader, CardTitle, CardContent } from "@src/components/ui/card";
import { Progress } from "@src/components/ui/progress";
import { Badge } from "@src/components/ui/badge";

/**
 * MetricsDisplay Component
 * Displays evaluation metrics with progress bars and badges
 * 
 * @param {Object} props
 * @param {Object} props.metrics - Metrics object with coverage, explainability, latency, auditability
 */
export default function MetricsDisplay({ metrics }) {
  if (!metrics) {
    return null;
  }

  const getPercentageColor = (percentage) => {
    if (percentage >= 95) return "bg-green-500";
    if (percentage >= 80) return "bg-yellow-500";
    return "bg-red-500";
  };

  const getPercentageVariant = (percentage) => {
    if (percentage >= 95) return "default";
    if (percentage >= 80) return "secondary";
    return "destructive";
  };

  const formatLatency = (ms) => {
    if (!ms && ms !== 0) return "N/A";
    if (ms < 1000) return `${Math.round(ms)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const coveragePercentage = metrics.coverage?.coverage_percentage || 0;
  const explainabilityPercentage = metrics.explainability?.explainability_percentage || 0;
  const avgLatency = metrics.latency?.avg_recommendation_latency_ms || null;
  const p95Latency = metrics.latency?.p95_recommendation_latency_ms || null;
  const auditabilityPercentage = metrics.auditability?.auditability_percentage || 0;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* Coverage Metric */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Coverage</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold">{coveragePercentage.toFixed(1)}%</span>
              <Badge variant={getPercentageVariant(coveragePercentage)}>
                {coveragePercentage >= 95 ? "Excellent" : coveragePercentage >= 80 ? "Good" : "Needs Improvement"}
              </Badge>
            </div>
            <Progress value={coveragePercentage} className="h-2" />
            <div className="text-xs text-muted-foreground">
              {metrics.coverage?.users_with_persona || 0} of {metrics.coverage?.total_users || 0} users with persona
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Explainability Metric */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Explainability</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold">{explainabilityPercentage.toFixed(1)}%</span>
              <Badge variant={getPercentageVariant(explainabilityPercentage)}>
                {explainabilityPercentage >= 95 ? "Excellent" : explainabilityPercentage >= 80 ? "Good" : "Needs Improvement"}
              </Badge>
            </div>
            <Progress value={explainabilityPercentage} className="h-2" />
            <div className="text-xs text-muted-foreground">
              {metrics.explainability?.recommendations_with_rationale || 0} of {metrics.explainability?.total_recommendations || 0} recommendations with rationale
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Latency Metric */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Average Latency</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold">{formatLatency(avgLatency)}</span>
              <Badge variant="outline">
                P95: {formatLatency(p95Latency)}
              </Badge>
            </div>
            <div className="text-xs text-muted-foreground">
              Average recommendation generation time
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Auditability Metric */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Auditability</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold">{auditabilityPercentage.toFixed(1)}%</span>
              <Badge variant={getPercentageVariant(auditabilityPercentage)}>
                {auditabilityPercentage >= 95 ? "Excellent" : auditabilityPercentage >= 80 ? "Good" : "Needs Improvement"}
              </Badge>
            </div>
            <Progress value={auditabilityPercentage} className="h-2" />
            <div className="text-xs text-muted-foreground">
              {metrics.auditability?.recommendations_with_traces || 0} recommendations with decision traces
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

