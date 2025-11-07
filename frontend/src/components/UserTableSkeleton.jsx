import { Skeleton } from './ui/skeleton';

/**
 * UserTableSkeleton Component
 * Shows loading skeleton for the user table
 */
export default function UserTableSkeleton() {
  return (
    <div className="rounded-md border">
      <div className="p-4">
        {/* Table Header */}
        <div className="flex gap-4 mb-4 pb-2 border-b">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-4 w-24 ml-auto" />
        </div>
        
        {/* Table Rows */}
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="flex gap-4 py-3 border-b last:border-0">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-4 w-48" />
            <Skeleton className="h-6 w-24 rounded-full" />
            <Skeleton className="h-6 w-20 rounded-full" />
            <Skeleton className="h-8 w-24 ml-auto rounded-md" />
          </div>
        ))}
      </div>
    </div>
  );
}

