import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/components"

const progressVariants = cva(
  "h-2 w-full overflow-hidden rounded-full bg-primary/20",
  {
    variants: {
      variant: {
        default: "bg-primary",
        destructive: "bg-destructive",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface ProgressProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof progressVariants> {
  value?: number
}

const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(
  ({ className, value = 0, variant = "default", ...props }, ref) => (
    <div
      ref={ref}
      className={cn(progressVariants({ variant }), className)}
      {...props}
    >
      <div
        className="h-full w-full flex-1 bg-primary transition-all"
        style={{ transform: `translateX(-${100 - (value || 0)}%)` }}
      />
    </div>
  )
)
Progress.displayName = "Progress"

export { Progress }
