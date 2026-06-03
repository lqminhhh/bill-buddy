import { useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Check, Copy, RotateCw } from "lucide-react"
import { toast } from "sonner"

import { api } from "@/api/client"
import { qk } from "@/api/queryKeys"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

interface ShareTripDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  tripId: number
  tripName: string
  shareToken: string | null | undefined
}

function buildShareUrl(token: string): string {
  return `${window.location.origin}/share/${token}`
}

export function ShareTripDialog({
  open,
  onOpenChange,
  tripId,
  tripName,
  shareToken,
}: ShareTripDialogProps) {
  const qc = useQueryClient()
  const [confirmRotate, setConfirmRotate] = useState(false)
  const [copied, setCopied] = useState(false)

  const rotate = useMutation({
    mutationFn: () => api.rotateShareToken(tripId),
    onSuccess: (trip) => {
      qc.setQueryData(qk.trip(tripId), (prev: typeof trip | undefined) =>
        prev ? { ...prev, share_token: trip.share_token } : prev
      )
      qc.invalidateQueries({ queryKey: qk.trip(tripId) })
      toast.success("New share link generated")
      setConfirmRotate(false)
    },
    onError: () => toast.error("Couldn't rotate the link"),
  })

  const url = shareToken ? buildShareUrl(shareToken) : ""

  const handleCopy = async () => {
    if (!url) return
    try {
      await navigator.clipboard.writeText(url)
      setCopied(true)
      toast.success("Link copied")
      setTimeout(() => setCopied(false), 2000)
    } catch {
      toast.error("Couldn't copy — copy it manually")
    }
  }

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Share &quot;{tripName}&quot;</DialogTitle>
            <DialogDescription>
              Anyone with this link can view the trip and add expenses — no
              account needed. Send it to your group chat.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div className="space-y-2">
              <Label htmlFor="share-url">Share link</Label>
              <div className="flex gap-2">
                <Input
                  id="share-url"
                  value={url}
                  readOnly
                  onFocus={(e) => e.currentTarget.select()}
                />
                <Button
                  type="button"
                  variant="secondary"
                  onClick={handleCopy}
                  disabled={!url}
                >
                  {copied ? <Check /> : <Copy />}
                  {copied ? "Copied" : "Copy"}
                </Button>
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              If the link leaks, rotate it — this invalidates the old URL and
              generates a new one.
            </p>
            <div className="flex justify-end">
              <Button
                type="button"
                variant="ghost"
                onClick={() => setConfirmRotate(true)}
                disabled={rotate.isPending}
              >
                <RotateCw />
                Rotate link
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <AlertDialog open={confirmRotate} onOpenChange={setConfirmRotate}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Rotate share link?</AlertDialogTitle>
            <AlertDialogDescription>
              The current link will stop working immediately. Anyone using it
              will need the new link to view this trip.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => rotate.mutate()}
              disabled={rotate.isPending}
            >
              Rotate
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
