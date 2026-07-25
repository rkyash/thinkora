/**
 * Barrel export for all UI primitives.
 * Import as: import { Button, Input } from '@/components/ui'
 *
 * NOTE: Keep individual named exports to allow tree-shaking.
 */
export { Button } from './Button'
export type { ButtonProps } from './Button'

export { Input } from './Input'
export type { InputProps } from './Input'

export { Textarea } from './Textarea'
export type { TextareaProps } from './Textarea'

export { Badge } from './Badge'
export type { BadgeProps } from './Badge'

export { Spinner, PageSpinner, InlineSpinner } from './Spinner'

export { Modal, ModalFooter } from './Modal'
export type { ModalProps } from './Modal'

export { ToastContainer, useToast } from './Toast'
export type { ToastMessage, ToastVariant } from './Toast'
