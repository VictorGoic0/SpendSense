import { useState, useEffect, useRef } from "react";
import { getOperatorDashboard, runEvaluation, getLatestEvaluation, getEvaluationHistory, getLatestExports } from "@src/lib/apiService";
import MetricsCard from "@src/components/MetricsCard";
import MetricsDisplay from "@src/components/MetricsDisplay";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@src/components/ui/card";
import { Skeleton } from "@src/components/ui/skeleton";
import { Alert, AlertTitle, AlertDescription } from "@src/components/ui/alert";
import { Button } from "@src/components/ui/button";
import { Badge } from "@src/components/ui/badge";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { RefreshCw, Download, Play } from "lucide-react";

export default function OperatorDashboard() {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Evaluation state
  const [evaluationMetrics, setEvaluationMetrics] = useState(null);
  const [evaluationLoading, setEvaluationLoading] = useState(false);
  const [evaluationError, setEvaluationError] = useState(null);
  const [evaluationHistory, setEvaluationHistory] = useState([]);
  const [exports, setExports] = useState([]);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);
  const autoRefreshIntervalRef = useRef(null);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getOperatorDashboard();
      setDashboardData(data);
    } catch (err) {
      setError(err.message || "Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  };

  const fetchLatestEvaluation = async () => {
    try {
      const data = await getLatestEvaluation();
      setEvaluationMetrics(data);
      setLastUpdated(new Date());
      setEvaluationError(null);
    } catch (err) {
      // If no evaluation exists yet, that's okay
      if (err.response?.status !== 404) {
        setEvaluationError(err.message || "Failed to load evaluation metrics");
      }
    }
  };

  const fetchEvaluationHistory = async () => {
    try {
      const data = await getEvaluationHistory(5);
      setEvaluationHistory(data.runs || []);
    } catch (err) {
      console.error("Failed to load evaluation history:", err);
    }
  };

  const fetchExports = async () => {
    try {
      const data = await getLatestExports(10);
      setExports(data.exports || []);
    } catch (err) {
      console.error("Failed to load exports:", err);
    }
  };

  const handleRunEvaluation = async () => {
    try {
      setEvaluationLoading(true);
      setEvaluationError(null);
      const result = await runEvaluation();
      setEvaluationMetrics(result.metrics);
      setLastUpdated(new Date());
      
      // Refresh history and exports after running evaluation
      await fetchEvaluationHistory();
      await fetchExports();
      
      // Show success message (using alert for now, could be replaced with toast)
      alert("Evaluation completed successfully!");
    } catch (err) {
      setEvaluationError(err.message || "Failed to run evaluation");
      alert(`Error: ${err.message || "Failed to run evaluation"}`);
    } finally {
      setEvaluationLoading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return "N/A";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const formatTimestamp = (dateString) => {
    if (!dateString) return "N/A";
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? "s" : ""} ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? "s" : ""} ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays} day${diffDays > 1 ? "s" : ""} ago`;
  };

  // Auto-refresh evaluation metrics every 60 seconds
  useEffect(() => {
    if (autoRefreshEnabled) {
      // Initial fetch
      fetchLatestEvaluation();
      fetchEvaluationHistory();
      fetchExports();

      // Set up interval
      autoRefreshIntervalRef.current = setInterval(() => {
        fetchLatestEvaluation();
        fetchEvaluationHistory();
        fetchExports();
      }, 60000); // 60 seconds

      return () => {
        if (autoRefreshIntervalRef.current) {
          clearInterval(autoRefreshIntervalRef.current);
        }
      };
    }
  }, [autoRefreshEnabled]);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  // Transform persona distribution for chart
  const personaChartData = dashboardData?.persona_distribution
    ? Object.entries(dashboardData.persona_distribution).map(([name, value]) => ({
        name: name
          .split("_")
          .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
          .join(" "),
        value,
      }))
    : [];

  // Transform recommendation status for chart
  const recommendationChartData = dashboardData?.recommendations
    ? Object.entries(dashboardData.recommendations).map(([name, value]) => ({
        name: name
          .split("_")
          .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
          .join(" "),
        value,
      }))
    : [];

  // Color scheme for recommendation status
  const getStatusColor = (name) => {
    const lowerName = name.toLowerCase();
    if (lowerName.includes("pending")) return "#3b82f6"; // blue
    if (lowerName.includes("approved")) return "#10b981"; // green
    if (lowerName.includes("overridden")) return "#f59e0b"; // amber
    if (lowerName.includes("rejected")) return "#ef4444"; // red
    return "#6b7280"; // gray
  };

  if (loading) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Operator Dashboard</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-16 mb-2" />
                <Skeleton className="h-3 w-32" />
              </CardContent>
            </Card>
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <Skeleton className="h-6 w-48" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-64 w-full" />
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <Skeleton className="h-6 w-48" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-64 w-full" />
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Operator Dashboard</h1>
        <Alert className="mb-4">
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
        <Button onClick={fetchDashboardData}>Retry</Button>
      </div>
    );
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Operator Dashboard</h1>
        <div className="flex gap-2">
          <Button
            onClick={handleRunEvaluation}
            disabled={evaluationLoading}
            className="flex items-center gap-2"
          >
            {evaluationLoading ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                Running...
              </>
            ) : (
              <>
                <Play className="h-4 w-4" />
                Run Evaluation
              </>
            )}
          </Button>
          <Button
            variant="outline"
            onClick={() => {
              fetchLatestEvaluation();
              fetchEvaluationHistory();
              fetchExports();
            }}
            className="flex items-center gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Evaluation Metrics Section */}
      {evaluationError && (
        <Alert className="mb-4 border-red-500 bg-red-50">
          <AlertTitle className="text-red-900">Evaluation Error</AlertTitle>
          <AlertDescription className="text-red-800">{evaluationError}</AlertDescription>
        </Alert>
      )}

      {evaluationMetrics && (
        <div className="mb-6">
          <div className="flex justify-between items-center mb-4">
            <div className="flex-1 text-left">
              <h2 className="text-2xl font-semibold text-gray-900 text-left">Evaluation Metrics</h2>
              {lastUpdated && (
                <p className="text-sm text-muted-foreground text-left">
                  Last updated: {formatTimestamp(lastUpdated.toISOString())}
                </p>
              )}
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="auto-refresh"
                checked={autoRefreshEnabled}
                onChange={(e) => setAutoRefreshEnabled(e.target.checked)}
                className="rounded"
              />
              <label htmlFor="auto-refresh" className="text-sm text-muted-foreground">
                Auto-refresh (60s)
              </label>
            </div>
          </div>
          <MetricsDisplay metrics={evaluationMetrics} />
        </div>
      )}

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <MetricsCard
          title="Total Users"
          value={dashboardData?.total_users || 0}
          subtitle="All registered users"
        />
        <MetricsCard
          title="Users with Consent"
          value={dashboardData?.users_with_consent || 0}
          subtitle={`${dashboardData?.total_users ? Math.round((dashboardData.users_with_consent / dashboardData.total_users) * 100) : 0}% of total`}
        />
        <MetricsCard
          title="Pending Approvals"
          value={dashboardData?.recommendations?.pending_approval || 0}
          subtitle="Awaiting review"
        />
        <MetricsCard
          title="Avg Latency"
          value={`${dashboardData?.metrics?.avg_latency_ms || 0}ms`}
          subtitle="Average response time"
        />
      </div>

      {/* Download Links Section */}
      {exports.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Parquet Exports</CardTitle>
            <CardDescription>Download evaluation data and user features</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {exports.map((exportItem, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50"
                >
                  <div className="flex-1">
                    <div className="font-medium text-sm">{exportItem.key.split('/').pop()}</div>
                    <div className="text-xs text-muted-foreground">
                      {formatFileSize(exportItem.size)} • {formatDate(exportItem.last_modified)}
                    </div>
                  </div>
                  {exportItem.download_url ? (
                    <Button
                      variant="outline"
                      size="sm"
                      asChild
                      className="flex items-center gap-2"
                    >
                      <a href={exportItem.download_url} download target="_blank" rel="noopener noreferrer">
                        <Download className="h-4 w-4" />
                        Download
                      </a>
                    </Button>
                  ) : (
                    <Badge variant="secondary">Unavailable</Badge>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Evaluation History Section */}
      {evaluationHistory.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Evaluation History</CardTitle>
            <CardDescription>Last 5 evaluation runs</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {evaluationHistory.map((run, index) => (
                <div
                  key={run.metric_id || index}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50"
                >
                  <div className="flex-1">
                    <div className="font-medium text-sm">{run.run_id}</div>
                    <div className="text-xs text-muted-foreground">
                      {formatDate(run.timestamp)}
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className="text-xs text-muted-foreground">Coverage</div>
                      <div className="text-sm font-medium">
                        {run.coverage_percentage?.toFixed(1) || "N/A"}%
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-muted-foreground">Explainability</div>
                      <div className="text-sm font-medium">
                        {run.explainability_percentage?.toFixed(1) || "N/A"}%
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-muted-foreground">Latency</div>
                      <div className="text-sm font-medium">
                        {run.avg_recommendation_latency_ms ? `${Math.round(run.avg_recommendation_latency_ms)}ms` : "N/A"}
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        // For now, just show an alert with details
                        // Could be expanded to show a modal with full details
                        alert(`Run ID: ${run.run_id}\nTimestamp: ${formatDate(run.timestamp)}\nCoverage: ${run.coverage_percentage?.toFixed(1)}%\nExplainability: ${run.explainability_percentage?.toFixed(1)}%\nLatency: ${run.avg_recommendation_latency_ms ? `${Math.round(run.avg_recommendation_latency_ms)}ms` : "N/A"}`);
                      }}
                    >
                      View Details
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Persona Distribution Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Persona Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={personaChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="name"
                  angle={-45}
                  textAnchor="end"
                  height={100}
                  tick={{ fontSize: 12 }}
                />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Recommendation Status Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Recommendation Status</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={recommendationChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="name"
                  angle={-45}
                  textAnchor="end"
                  height={100}
                  tick={{ fontSize: 12 }}
                />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value">
                  {recommendationChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={getStatusColor(entry.name)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
