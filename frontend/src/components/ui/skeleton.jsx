import * as React from "react"
import { cn } from "@src/lib/utils"

const Skeleton = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("animate-pulse rounded-md bg-gray-200", className)}
    {...props}
  />
))
Skeleton.displayName = "Skeleton"

export { Skeleton }

