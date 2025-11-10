import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@src/components/ui/dialog";
import { Button } from "@src/components/ui/button";
import { CheckCircle2 } from "lucide-react";

/**
 * SuccessModal Component
 * A simple modal to display success messages
 * 
 * @param {Object} props
 * @param {boolean} props.open - Whether the modal is open
 * @param {function} props.onClose - Function to call when closing the modal
 * @param {string} props.title - Title of the modal (default: "Success")
 * @param {string} props.message - Message to display
 */
export default function SuccessModal({ open, onClose, title = "Success", message }) {
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-3 mb-2">
            <CheckCircle2 className="h-6 w-6 text-green-500" />
            <DialogTitle className="text-left">{title}</DialogTitle>
          </div>
          <DialogDescription className="text-left">
            {message}
          </DialogDescription>
        </DialogHeader>
        <div className="flex justify-end mt-4">
          <Button onClick={onClose}>Close</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

