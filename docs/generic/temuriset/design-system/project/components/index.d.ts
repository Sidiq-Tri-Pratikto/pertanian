// TemuRiset Design System 1.0.0-draft — window.TR. Documentation types; the bundle is plain JS.
import type * as React from 'react';

type Node = React.ReactNode;
/** Decimal money as a string, so values never pass through floating point. null means unknown, never zero. */
export type Decimal = string | null;
export type Tone = 'neutral' | 'success' | 'danger' | 'warning' | 'action';
export type IconName = 'check' | 'cross' | 'question' | 'minus' | 'alert' | 'clock' | 'lock' | 'shield' | 'file' | 'upload' | 'external' | 'down' | 'right' | 'left' | 'arrow' | 'close' | 'user' | 'building' | 'search' | 'home' | 'bulb' | 'chat' | 'inbox' | 'calendar' | 'more' | 'refresh' | 'edit' | 'eye' | 'eyeOff' | 'partner';

/* ---------- primitives ---------- */
export interface ButtonProps {
  children: Node;
  intent?: 'primary' | 'secondary' | 'danger';
  onClick?: (e: React.MouseEvent) => void;
  type?: 'button' | 'submit';
  icon?: IconName;
  /** Shows a spinner and busyLabel; repeat clicks are ignored. Never announces success. */
  busy?: boolean;
  busyLabel?: string;
  /** Non-empty = disabled. The control stays focusable and the reason is visible and linked. */
  disabledReason?: string | null;
  fullWidth?: boolean;
  id?: string; form?: string; describedBy?: string;
}
export declare function Button(props: ButtonProps): React.ReactElement;

export interface LinkProps { children: Node; href?: string; external?: boolean; /** Hidden text naming the field, e.g. "judul inovasi". */ context?: string; onClick?: (e: React.MouseEvent) => void; id?: string; }
export declare function Link(props: LinkProps): React.ReactElement;

interface FieldProps { label: Node; hint?: Node; required?: boolean; error?: string | null; errorCode?: string; id?: string; name?: string; describedBy?: string; }
export interface TextFieldProps extends FieldProps { value?: string; onChange?: (value: string) => void; type?: 'text' | 'email' | 'decimal'; prefix?: Node; suffix?: Node; autoComplete?: string; }
export declare function TextField(props: TextFieldProps): React.ReactElement;
export interface TextAreaProps extends FieldProps { value?: string; onChange?: (value: string) => void; rows?: number; /** Soft limit: text is kept and the count says how far over it is. */ limit?: number; }
export declare function TextArea(props: TextAreaProps): React.ReactElement;
export interface SelectProps extends FieldProps { value?: string; onChange?: (value: string) => void; options: { value: string; label: string; disabledReason?: string }[]; /** null removes the empty choice. */ emptyLabel?: string | null; }
export declare function Select(props: SelectProps): React.ReactElement;
export interface ChoiceGroupProps { legend: Node; options: { value: string; label: Node; hint?: Node; disabledReason?: string }[]; value?: string; onChange?: (value: string) => void; hint?: Node; required?: boolean; error?: string | null; /** Id of the first radio, for ErrorSummary links. */ id?: string; name?: string; }
export declare function ChoiceGroup(props: ChoiceGroupProps): React.ReactElement;
export interface CheckboxProps { label: Node; checked?: boolean; onChange?: (checked: boolean) => void; hint?: Node; disabledReason?: string; error?: string | null; id?: string; name?: string; }
export declare function Checkbox(props: CheckboxProps): React.ReactElement;
export interface FieldErrorProps { children: Node; id?: string; code?: string; }
export declare function FieldError(props: FieldErrorProps): React.ReactElement;
export interface ErrorSummaryProps { errors?: { fieldId: string; message: string }[]; /** Change on each failed attempt; focus moves only then. */ focusKey?: number; title?: string; children?: Node; retry?: { label: string; onClick: () => void }; id?: string; }
export declare function ErrorSummary(props: ErrorSummaryProps): React.ReactElement;
export interface DialogProps { open: boolean; onClose: () => void; title: Node; children: Node; primary?: { label: string; onClick: () => void; busy?: boolean; busyLabel?: string; intent?: 'primary' | 'danger'; disabledReason?: string }; secondary?: { label: string; onClick?: () => void }; initialFocusId?: string; returnFocusId?: string; }
export declare function Dialog(props: DialogProps): React.ReactElement;
export interface DisclosureProps { label: Node; children: Node; defaultOpen?: boolean; /** sessionStorage key that keeps the state when returning. */ storageKey?: string; }
export declare function Disclosure(props: DisclosureProps): React.ReactElement;
export interface TabsProps { label: string; tabs: { id: string; label: string; content: Node }[]; value?: string; onChange?: (id: string) => void; }
export declare function Tabs(props: TabsProps): React.ReactElement;
export interface StatusProps { label: string; tone?: Tone; icon?: IconName | null; children?: Node; live?: boolean | 'alert'; }
export declare function Status(props: StatusProps): React.ReactElement;
export interface EmptyStateProps { kind?: 'noInventions' | 'noMatches' | 'closedIntake' | 'denied'; title?: string; icon?: IconName; children?: Node; action?: Node; }
export declare function EmptyState(props: EmptyStateProps): React.ReactElement;
export interface SaveStateProps { state: 'local' | 'saving' | 'saved' | 'failed' | 'conflict'; location?: 'demo' | 'server'; savedAt?: string; timeZone?: string; onRetry?: () => void; }
export declare function SaveState(props: SaveStateProps): React.ReactElement;
export interface PartyContext { id: string; kind: 'personal' | 'organization'; name: string; disabledReason?: string; }
export interface ContextSwitcherProps { value: string; options: PartyContext[]; onChange?: (id: string) => void; readOnly?: boolean; actionLabel?: string; label?: string; hint?: Node; id?: string; }
export declare function ContextSwitcher(props: ContextSwitcherProps): React.ReactElement;

/* ---------- domain ---------- */
export interface FinancialScopeProps { subject: 'project' | 'companyTarget' | 'contribution' | 'investorCheck' | 'partner' | 'license'; label?: string; currency?: string; min?: Decimal; max?: Decimal; period?: string; scope?: string; estimateDate?: string; assumptions?: string; /** Replaces the amount for noncash support. */ noncash?: string; terms?: string; compact?: boolean; edit?: Node; }
export declare function FinancialScope(props: FinancialScopeProps): React.ReactElement;
export interface InventionCardProps { title: string; category: string; image?: { src: string; alt: string }; manager?: string; problem?: Node; solution?: Node; maturity?: string; support?: string; financial?: FinancialScopeProps; facts?: Node; reasons?: string[]; gap?: Node; action?: Node; }
export declare function InventionCard(props: InventionCardProps): React.ReactElement;
export interface FundingRequestCardProps { company: string; proposedEntity?: boolean; stage?: string; form?: string; purpose?: string; currency: string; target: Decimal; desiredMin?: Decimal; desiredMax?: Decimal; partialAccepted?: boolean; inventions?: string[]; reasons?: string[]; gap?: Node; action?: Node; }
export declare function FundingRequestCard(props: FundingRequestCardProps): React.ReactElement;
export interface RequirementRowProps { label: string; result: 'PASS' | 'FAIL' | 'UNKNOWN' | 'NOT_APPLICABLE'; stage?: 'SUBMISSION' | 'DISCUSSION' | 'PILOT' | 'COMMERCIALIZATION'; mandatory?: boolean; mode?: 'DECLARATION' | 'DOCUMENT_PRESENT' | 'REVIEWER_CONFIRMED'; reason?: Node; source?: string; action?: Node; }
export declare function RequirementRow(props: RequirementRowProps): React.ReactElement;
export interface FactSourceProps { value?: string; timing?: 'CURRENT' | 'PLANNED' | 'REQUESTED'; provenance?: 'SOURCE_REPORTED' | 'SELF_DECLARED' | 'PROVIDED' | 'REVIEWED' | 'UNKNOWN'; reviewScope?: string; sourceHref?: string; sourceLabel?: string; }
export declare function FactSource(props: FactSourceProps): React.ReactElement;
export interface DocumentItemProps { title?: string; version?: number; file?: 'CREATED' | 'UPLOADING' | 'QUARANTINED' | 'AVAILABLE' | 'REJECTED'; extraction?: 'NOT_REQUESTED' | 'PENDING' | 'RUNNING' | 'SUCCEEDED' | 'FAILED' | 'NEEDS_MANUAL_INPUT'; review?: 'PROVIDED_UNREVIEWED' | 'REVIEWED_SUPPORTED' | 'REVIEWED_UNSUPPORTED' | 'NEEDS_CLARIFICATION' | 'EXPIRED' | 'SUPERSEDED'; grant?: { recipient: string; version?: number; revoked?: boolean } | null; denied?: boolean; action?: Node; }
export declare function DocumentItem(props: DocumentItemProps): React.ReactElement;
export interface RevisionItemProps { round?: number; index?: number; question: string; reason?: string; required?: boolean; due?: string; value?: { response?: 'CAN' | 'DISCUSS' | 'CANNOT'; text?: string }; onChange?: (value: { response?: string; text?: string }) => void; attachments?: Node; review?: Node; error?: string | null; id?: string; }
export declare function RevisionItem(props: RevisionItemProps): React.ReactElement;
export interface ScheduleSlot { id: string; /** UTC ISO instant. */ start: string; minutes: number; conflict?: boolean; }
export interface ScheduleSlotListProps { slots: ScheduleSlot[]; zone?: string; otherZone?: string; selectedId?: string | null; onSelect?: (id: string) => void; confirmedId?: string | null; state?: 'open' | 'expired' | 'superseded' | 'cancelled'; onConfirm?: () => void; onPropose?: () => void; busy?: boolean; agenda?: string; error?: Node; }
export declare function ScheduleSlotList(props: ScheduleSlotListProps): React.ReactElement;
export interface ConsentParty { name: string; selected: string[]; confirmedVersion: number | null; }
export interface PartnershipConsentProps { version: number; type?: string; summary?: Node; fields: { id: string; label: string; value?: string }[]; mine: ConsentParty; other: ConsentParty; restricted?: string[]; onToggle?: (id: string, checked: boolean) => void; onConfirm?: () => void; onRequestChange?: () => void; onRestrict?: (id: string) => void; busy?: boolean; readOnly?: boolean; error?: Node; }
export declare function PartnershipConsent(props: PartnershipConsentProps): React.ReactElement;
export interface VersionConflictProps { what: Node; currentVersion?: string; draft?: string; onRefresh?: () => void; refreshLabel?: string; onCopy?: () => void; onCompare?: () => void; }
export declare function VersionConflict(props: VersionConflictProps): React.ReactElement;

/* ---------- intentional additions ---------- */
export interface NextStepProps { who?: 'you' | 'other'; title: string; children?: Node; due?: string; action?: Node; }
export declare function NextStep(props: NextStepProps): React.ReactElement;
export interface StepsProps { steps: { id: string; label: string; done?: boolean }[]; current: string; onSelect?: (id: string) => void; label?: string; }
export declare function Steps(props: StepsProps): React.ReactElement;
export interface SummaryListProps { rows: { id: string; label: string; value: Node; onChange?: () => void }[]; }
export declare function SummaryList(props: SummaryListProps): React.ReactElement;
export interface ScreenProps { persona?: 'inovator' | 'mitra'; current?: string; onNavigate?: (id: string) => void; title: string; subtitle?: Node; back?: Node; save?: Node; next?: Node; aside?: Node; context?: Node; provenance?: string; children?: Node; }
export declare function Screen(props: ScreenProps): React.ReactElement;
export interface IconProps { name: IconName; size?: 'small'; className?: string; }
export declare function Icon(props: IconProps): React.ReactElement;
