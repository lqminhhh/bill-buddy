import { Link } from "react-router-dom"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"

export function PlaceholderPage({ title }: { title: string }) {
  return (
    <Card>
      <CardContent className="space-y-3 py-10">
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        <p className="text-sm text-muted-foreground">
          This page is coming in the next batch. The plumbing (routing, API client,
          dark mode, design system) is already wired up — only this screen still
          needs to be built.
        </p>
        <Button asChild variant="secondary">
          <Link to="/">Back to trips</Link>
        </Button>
      </CardContent>
    </Card>
  )
}
