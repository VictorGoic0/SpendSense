import { useState, useEffect, useRef, useCallback } from "react";
import {
  getApprovalQueue,
  approveRecommendation,
  bulkApprove,
  overrideRecommendation,
  rejectRecommendation,
} from "@src/lib/apiService";
import RecommendationCard from "@src/components/RecommendationCard";
import ProductRecommendationCard from "@src/components/ProductRecommendationCard";
import { Button } from "@src/components/ui/button";
import { Card, CardContent } from "@src/components/ui/card";
import { Alert, AlertTitle, AlertDescription } from "@src/components/ui/alert";
import { Skeleton } from "@src/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@src/components/ui/dialog";
import { Checkbox } from "@src/components/ui/checkbox";
import { RefreshCw, CheckCircle2, XCircle } from "lucide-react";

// Temporary operator ID - in production this would come from auth context
const OPERATOR_ID = "operator_1";

export default function OperatorApprovalQueue() {
  const [recommendations, setRecommendations] = useState([]);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState("pending_approval");
  const [actionLoading, setActionLoading] = useState({});
  const [successMessage, setSuccessMessage] = useState(null);
  const [overrideDialogOpen, setOverrideDialogOpen] = useState(false);
  const [rejectDialogOpen, setRejectDialogOpen] = useState(false);
  const [selectedRecommendation, setSelectedRecommendation] = useState(null);
  const [overrideForm, setOverrideForm] = useState({
    newTitle: "",
    newContent: "",
    reason: "",
  });
  const [overrideFormError, setOverrideFormError] = useState(null);
  const [rejectForm, setRejectForm] = useState({ reason: "" });
  const [rejectFormError, setRejectFormError] = useState(null);
  const refreshIntervalRef = useRef(null);

  // Fetch recommendations
  const fetchRecommendations = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getApprovalQueue(statusFilter);
      setRecommendations(data.recommendations || []);
    } catch (err) {
      setError(err.message || "Failed to load approval queue");
      console.error("Error fetching approval queue:", err);
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  // Initial fetch and auto-refresh
  useEffect(() => {
    fetchRecommendations();

    // Auto-refresh every 30 seconds
    refreshIntervalRef.current = setInterval(() => {
      fetchRecommendations();
    }, 30000);

    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, [fetchRecommendations]);

  // Clear success message after 5 seconds
  useEffect(() => {
    if (successMessage) {
      const timer = setTimeout(() => setSuccessMessage(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [successMessage]);

  // Handle individual selection
  const handleSelect = (recId, checked) => {
    const newSelected = new Set(selectedIds);
    if (checked) {
      newSelected.add(recId);
    } else {
      newSelected.delete(recId);
    }
    setSelectedIds(newSelected);
  };

  // Handle select all
  const handleSelectAll = (checked) => {
    if (checked) {
      const allIds = new Set(recommendations.map((r) => r.recommendation_id));
      setSelectedIds(allIds);
    } else {
      setSelectedIds(new Set());
    }
  };

  // Handle individual approve
  const handleApprove = async (recommendation) => {
    const recId = recommendation.recommendation_id;
    setActionLoading((prev) => ({ ...prev, [recId]: true }));

    try {
      await approveRecommendation(recId, OPERATOR_ID);
      setSuccessMessage(`Recommendation "${recommendation.title}" approved successfully`);
      // Remove from list or update status
      setRecommendations((prev) =>
        prev.filter((r) => r.recommendation_id !== recId)
      );
      setSelectedIds((prev) => {
        const newSet = new Set(prev);
        newSet.delete(recId);
        return newSet;
      });
    } catch (err) {
      setError(err.message || "Failed to approve recommendation");
      console.error("Error approving recommendation:", err);
    } finally {
      setActionLoading((prev) => ({ ...prev, [recId]: false }));
    }
  };

  // Handle bulk approve
  const handleBulkApprove = async () => {
    if (selectedIds.size === 0) return;

    setActionLoading((prev) => ({ ...prev, bulk: true }));

    try {
      const recIds = Array.from(selectedIds);
      const result = await bulkApprove(OPERATOR_ID, recIds);
      setSuccessMessage(
        `Successfully approved ${result.approved} recommendation(s). ${result.failed > 0 ? `${result.failed} failed.` : ""}`
      );
      // Refresh recommendations
      await fetchRecommendations();
      setSelectedIds(new Set());
    } catch (err) {
      setError(err.message || "Failed to bulk approve recommendations");
      console.error("Error bulk approving:", err);
    } finally {
      setActionLoading((prev) => ({ ...prev, bulk: false }));
    }
  };

  // Handle override
  const handleOverrideClick = (recommendation) => {
    setSelectedRecommendation(recommendation);
    setOverrideForm({
      newTitle: "",
      newContent: "",
      reason: "",
    });
    setOverrideFormError(null);
    setOverrideDialogOpen(true);
  };

  const handleOverrideSubmit = async () => {
    // Validate reason is provided
    if (!overrideForm.reason.trim()) {
      setOverrideFormError("Reason is required for override");
      return;
    }

    // Validate at least one of new title or new content is provided
    if (!overrideForm.newTitle && !overrideForm.newContent) {
      setOverrideFormError("At least one of new title or new content must be provided");
      return;
    }

    const recId = selectedRecommendation.recommendation_id;
    setActionLoading((prev) => ({ ...prev, [recId]: true }));
    setOverrideFormError(null);

    try {
      await overrideRecommendation(
        recId,
        OPERATOR_ID,
        overrideForm.reason,
        overrideForm.newTitle || null,
        overrideForm.newContent || null
      );
      setSuccessMessage(`Recommendation "${selectedRecommendation.title}" overridden successfully`);
      setOverrideDialogOpen(false);
      await fetchRecommendations();
    } catch (err) {
      setOverrideFormError(err.message || "Failed to override recommendation");
      console.error("Error overriding recommendation:", err);
    } finally {
      setActionLoading((prev) => ({ ...prev, [recId]: false }));
    }
  };

  // Handle reject
  const handleRejectClick = (recommendation) => {
    setSelectedRecommendation(recommendation);
    setRejectForm({ reason: "" });
    setRejectFormError(null);
    setRejectDialogOpen(true);
  };

  const handleRejectSubmit = async () => {
    // Validate reason is provided
    if (!rejectForm.reason.trim()) {
      setRejectFormError("Reason is required for rejection");
      return;
    }

    const recId = selectedRecommendation.recommendation_id;
    setActionLoading((prev) => ({ ...prev, [recId]: true }));
    setRejectFormError(null);

    try {
      await rejectRecommendation(recId, OPERATOR_ID, rejectForm.reason);
      setSuccessMessage(`Recommendation "${selectedRecommendation.title}" rejected successfully`);
      setRejectDialogOpen(false);
      // Remove from list
      setRecommendations((prev) =>
        prev.filter((r) => r.recommendation_id !== recId)
      );
      setSelectedIds((prev) => {
        const newSet = new Set(prev);
        newSet.delete(recId);
        return newSet;
      });
    } catch (err) {
      setRejectFormError(err.message || "Failed to reject recommendation");
      console.error("Error rejecting recommendation:", err);
    } finally {
      setActionLoading((prev) => ({ ...prev, [recId]: false }));
    }
  };

  const allSelected = recommendations.length > 0 && selectedIds.size === recommendations.length;
  const someSelected = selectedIds.size > 0 && selectedIds.size < recommendations.length;

  return (
    <div className="px-4 py-6 sm:px-0">
      {/* Page Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Approval Queue</h1>
        <Button
          variant="outline"
          size="sm"
          onClick={fetchRecommendations}
          disabled={loading}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {/* Success/Error Messages */}
      {successMessage && (
        <Alert className="mb-4 border-green-200 bg-green-50">
          <CheckCircle2 className="h-4 w-4 text-green-600" />
          <AlertTitle className="text-green-800">Success</AlertTitle>
          <AlertDescription className="text-green-700">
            {successMessage}
          </AlertDescription>
        </Alert>
      )}

      {error && (
        <Alert className="mb-4 border-red-200 bg-red-50">
          <XCircle className="h-4 w-4 text-red-600" />
          <AlertTitle className="text-red-800">Error</AlertTitle>
          <AlertDescription className="text-red-700">
            {error}
          </AlertDescription>
        </Alert>
      )}

      {/* Toolbar */}
      <div className="mb-6 flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Checkbox
              checked={allSelected}
              onCheckedChange={handleSelectAll}
              disabled={loading || recommendations.length === 0}
            />
            <label className="text-sm font-medium text-gray-700">
              Select All {someSelected && "(partial)"}
            </label>
          </div>
          {selectedIds.size > 0 && (
            <span className="text-sm text-gray-600">
              {selectedIds.size} selected
            </span>
          )}
        </div>

        <div className="flex items-center gap-4">
          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          >
            <option value="pending_approval">Pending Approval</option>
            <option value="overridden">Overridden</option>
            <option value="rejected">Rejected</option>
          </select>

          {/* Bulk Approve Button */}
          <Button
            onClick={handleBulkApprove}
            disabled={selectedIds.size === 0 || actionLoading.bulk}
          >
            {actionLoading.bulk ? (
              <>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                Approving...
              </>
            ) : (
              <>
                Bulk Approve ({selectedIds.size})
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <Skeleton className="h-6 w-3/4 mb-4" />
                <Skeleton className="h-4 w-full mb-2" />
                <Skeleton className="h-4 w-5/6" />
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!loading && recommendations.length === 0 && (
        <Card>
          <CardContent className="p-12 text-center">
            <p className="text-gray-500 text-lg">
              No recommendations in the queue
            </p>
            <p className="text-gray-400 text-sm mt-2">
              All recommendations have been processed
            </p>
          </CardContent>
        </Card>
      )}

      {/* Recommendations List */}
      {!loading && recommendations.length > 0 && (
        <div className="space-y-4">
          {recommendations.map((recommendation) => {
            const isProduct = recommendation.content_type === 'partner_offer';
            
            if (isProduct) {
              return (
                <ProductRecommendationCard
                  key={recommendation.recommendation_id}
                  recommendation={recommendation}
                  onApprove={handleApprove}
                  onReject={handleRejectClick}
                  onOverride={handleOverrideClick}
                  onSelect={handleSelect}
                  isSelected={selectedIds.has(recommendation.recommendation_id)}
                  isLoading={actionLoading[recommendation.recommendation_id]}
                />
              );
            }
            
            return (
              <RecommendationCard
                key={recommendation.recommendation_id}
                recommendation={recommendation}
                onApprove={handleApprove}
                onReject={handleRejectClick}
                onOverride={handleOverrideClick}
                onSelect={handleSelect}
                isSelected={selectedIds.has(recommendation.recommendation_id)}
                isLoading={actionLoading[recommendation.recommendation_id]}
              />
            );
          })}
        </div>
      )}

      {/* Override Dialog */}
      <Dialog open={overrideDialogOpen} onOpenChange={setOverrideDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Override Recommendation</DialogTitle>
            <DialogDescription>
              Modify the title and/or content of this recommendation. Original content will be preserved.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">
                New Title (optional)
              </label>
              <input
                type="text"
                value={overrideForm.newTitle}
                onChange={(e) =>
                  setOverrideForm({ ...overrideForm, newTitle: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder={selectedRecommendation?.title}
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">
                New Content (optional)
              </label>
              <textarea
                value={overrideForm.newContent}
                onChange={(e) =>
                  setOverrideForm({ ...overrideForm, newContent: e.target.value })
                }
                rows={6}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder={selectedRecommendation?.content?.substring(0, 200) + "..."}
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">
                Reason <span className="text-red-500">*</span>
              </label>
              {overrideFormError && (
                <p className="text-sm text-red-600 italic mb-1">
                  {overrideFormError}
                </p>
              )}
              <textarea
                value={overrideForm.reason}
                onChange={(e) => {
                  setOverrideForm({ ...overrideForm, reason: e.target.value });
                  // Clear error when user starts typing
                  if (overrideFormError) {
                    setOverrideFormError(null);
                  }
                }}
                rows={3}
                required
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  overrideFormError ? "border-red-300" : "border-gray-300"
                }`}
                placeholder="Explain why you're overriding this recommendation..."
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setOverrideDialogOpen(false);
                setOverrideFormError(null);
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={handleOverrideSubmit}
              disabled={actionLoading[selectedRecommendation?.recommendation_id]}
            >
              {actionLoading[selectedRecommendation?.recommendation_id] ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Overriding...
                </>
              ) : (
                "Override"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Reject Dialog */}
      <Dialog open={rejectDialogOpen} onOpenChange={setRejectDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reject Recommendation</DialogTitle>
            <DialogDescription>
              Provide a reason for rejecting this recommendation. This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <label className="text-sm font-medium text-gray-700 mb-1 block">
              Reason <span className="text-red-500">*</span>
            </label>
            {rejectFormError && (
              <p className="text-sm text-red-600 italic mb-1">
                {rejectFormError}
              </p>
            )}
            <textarea
              value={rejectForm.reason}
              onChange={(e) => {
                setRejectForm({ ...rejectForm, reason: e.target.value });
                // Clear error when user starts typing
                if (rejectFormError) {
                  setRejectFormError(null);
                }
              }}
              rows={4}
              required
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                rejectFormError ? "border-red-300" : "border-gray-300"
              }`}
              placeholder="Explain why you're rejecting this recommendation..."
            />
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setRejectDialogOpen(false);
                setRejectFormError(null);
              }}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleRejectSubmit}
              disabled={actionLoading[selectedRecommendation?.recommendation_id]}
            >
              {actionLoading[selectedRecommendation?.recommendation_id] ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Rejecting...
                </>
              ) : (
                "Reject"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
