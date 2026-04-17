import { useMemo, useState } from "react";
import { Copy, PhoneOff, SlidersHorizontal } from "lucide-react";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { ChatInput } from "@/features/chat/ChatInput";
import { ChatMessages } from "@/features/chat/ChatMessages";
import { DebugPane } from "@/features/chat/DebugPane";
import { useChat } from "@/features/chat/useChat";
import { cn } from "@/lib/utils";

function HangUpButton({ onHangUp }: { onHangUp: () => void }) {
  const [open, setOpen] = useState(false);
  return (
    <AlertDialog open={open} onOpenChange={setOpen}>
      <AlertDialogTrigger asChild>
        <Button size="sm" variant="destructive" className="gap-1.5">
          <PhoneOff className="size-3.5" />
          Hang up
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Hang up this call?</AlertDialogTitle>
          <AlertDialogDescription>
            The conversation will be cleared from the client. The backend
            session and summary are preserved.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={() => {
              setOpen(false);
              onHangUp();
            }}
          >
            Hang up
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

function NewSessionButton({
  onStart,
  hasSession,
  currentCallerPhone,
}: {
  onStart: (phone?: string) => void;
  hasSession: boolean;
  currentCallerPhone: string | undefined;
}) {
  const [open, setOpen] = useState(false);
  const [phone, setPhone] = useState(currentCallerPhone ?? "");
  const [confirmOpen, setConfirmOpen] = useState(false);

  const openDialog = () => {
    setPhone(currentCallerPhone ?? "");
    setOpen(true);
  };

  const submit = () => {
    const trimmed = phone.trim();
    onStart(trimmed || undefined);
    setOpen(false);
    setConfirmOpen(false);
  };

  const trigger = (
    <Button size="sm" variant="outline" onClick={hasSession ? () => setConfirmOpen(true) : openDialog}>
      New session
    </Button>
  );

  return (
    <>
      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogTrigger asChild>{trigger}</AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>End this call?</AlertDialogTitle>
            <AlertDialogDescription>
              The current session will be cleared from the client. The backend
              state is preserved.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                setConfirmOpen(false);
                openDialog();
              }}
            >
              End & start new
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogTrigger asChild>
          <span className="hidden" />
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>New session</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="caller-phone">Caller ID (optional)</Label>
              <Input
                id="caller-phone"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+1 555 555 5555"
                className="font-mono"
              />
              <p className="text-xs text-muted-foreground">
                Leave empty to simulate an anonymous call, or enter a known
                customer's phone to test the recognized-caller flow.
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button onClick={submit}>Start session</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

export function TestChatContainer() {
  const chat = useChat();
  const latencies = useMemo(
    () =>
      chat.messages
        .filter((m) => m.role === "assistant" && m.latencyMs)
        .map((m) => m.latencyMs!),
    [chat.messages],
  );

  return (
    <div className="flex h-full min-h-0 flex-col gap-4 lg:grid lg:grid-cols-[minmax(0,1fr)_320px]">
      <div className="flex min-h-0 flex-1 flex-col gap-3">
        {/* Session header */}
        <div className="flex shrink-0 flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            {chat.sessionId ? (
              <>
                <Badge variant="secondary" className="font-mono text-[11px]">
                  {chat.sessionId.slice(0, 12)}…
                </Badge>
                <Button
                  size="icon"
                  variant="ghost"
                  className="size-7"
                  onClick={() =>
                    navigator.clipboard.writeText(chat.sessionId!)
                  }
                  title="Copy full session id"
                >
                  <Copy className="size-3.5" />
                </Button>
                <Badge variant="outline" className="gap-1 tabular-nums">
                  <span className="text-muted-foreground">Turn</span>
                  <span className="font-medium">{chat.turnCount}</span>
                </Badge>
                {chat.callerPhone && (
                  <Badge
                    variant="outline"
                    className={cn("font-mono text-[11px]", "text-muted-foreground")}
                  >
                    {chat.callerPhone}
                  </Badge>
                )}
              </>
            ) : (
              <span className="text-xs text-muted-foreground">
                No active session — click <span className="font-medium text-foreground">Start session</span> to begin.
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Sheet>
              <SheetTrigger asChild>
                <Button variant="outline" size="sm" className="lg:hidden">
                  <SlidersHorizontal className="mr-1 size-4" />
                  Debug
                </Button>
              </SheetTrigger>
              <SheetContent side="right" className="w-96 overflow-auto">
                <DebugPane sessionId={chat.sessionId} latencies={latencies} />
              </SheetContent>
            </Sheet>
            {chat.sessionId && (
              <HangUpButton onHangUp={() => chat.newSession()} />
            )}
            <NewSessionButton
              hasSession={!!chat.sessionId}
              currentCallerPhone={chat.callerPhone}
              onStart={(phone) => {
                void chat.startSession(phone);
              }}
            />
          </div>
        </div>

        <div className="min-h-0 flex-1">
          <ChatMessages
            messages={chat.messages}
            pending={chat.pending}
            onStartSession={
              chat.sessionId || chat.pending
                ? undefined
                : () => void chat.startSession()
            }
            starting={chat.pending && !chat.sessionId}
          />
        </div>
        <div className="shrink-0">
          <ChatInput
            onSend={(t) => chat.send(t)}
            disabled={chat.pending || !chat.sessionId}
          />
        </div>
        {chat.error && (
          <p className="shrink-0 rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {chat.error}
          </p>
        )}
      </div>
      <aside className="hidden min-h-0 overflow-hidden lg:block">
        <DebugPane sessionId={chat.sessionId} latencies={latencies} />
      </aside>
    </div>
  );
}
