import { Badge } from '@/components/ui'
import type { SourceStatus } from '@/types/api'

interface Props {
  status: SourceStatus
}

export function SourceStatusBadge({ status }: Props) {
  switch (status) {
    case 'ready':
      return <Badge variant="success">Ready</Badge>
    case 'processing':
      return <Badge variant="warning">Processing...</Badge>
    case 'pending':
      return <Badge variant="default">Pending</Badge>
    case 'error':
      return <Badge variant="destructive">Error</Badge>
    default:
      return <Badge variant="outline">{status}</Badge>
  }
}
