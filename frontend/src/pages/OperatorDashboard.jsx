import { useState, useEffect } from "react";
import { getOperatorDashboard } from "@src/lib/apiService";
import MetricsCard from "@src/components/MetricsCard";
import { Card, CardHeader, CardTitle, CardContent } from "@src/components/ui/card";
import { Skeleton } from "@src/components/ui/skeleton";
import { Alert, AlertTitle, AlertDescription } from "@src/components/ui/alert";
import { Button } from "@src/components/ui/button";
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

export default function OperatorDashboard() {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Operator Dashboard</h1>

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
