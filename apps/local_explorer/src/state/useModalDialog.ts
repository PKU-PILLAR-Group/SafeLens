import { useEffect, useRef, type MutableRefObject, type RefObject } from "react";

const FOCUSABLE_SELECTOR = [
  "a[href]",
  "button:not([disabled])",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  "[tabindex]:not([tabindex='-1'])"
].join(",");

interface ModalDialogOptions {
  open: boolean;
  dialogRef: RefObject<HTMLElement>;
  initialFocusRef?: RefObject<HTMLElement>;
  returnFocusRef?: RefObject<HTMLElement>;
  restoreFocusRef?: MutableRefObject<boolean>;
  onClose: () => void;
}

function focusableElements(dialog: HTMLElement) {
  return Array.from(dialog.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)).filter(
    (element) => element.getClientRects().length > 0 && element.getAttribute("aria-hidden") !== "true"
  );
}

export function useModalDialog({
  open,
  dialogRef,
  initialFocusRef,
  returnFocusRef,
  restoreFocusRef,
  onClose
}: ModalDialogOptions) {
  const closeRef = useRef(onClose);
  closeRef.current = onClose;

  useEffect(() => {
    if (!open || !dialogRef.current) return;

    const dialog = dialogRef.current;
    if (restoreFocusRef) restoreFocusRef.current = true;
    const returnTarget = returnFocusRef?.current ?? (
      document.activeElement instanceof HTMLElement ? document.activeElement : null
    );
    const backgroundRegions = Array.from(
      document.querySelectorAll<HTMLElement>(".topbar, .workspace")
    ).map((element) => ({ element, wasInert: element.hasAttribute("inert") }));
    const previousOverflow = document.body.style.overflow;

    document.body.style.overflow = "hidden";
    for (const { element } of backgroundRegions) element.setAttribute("inert", "");

    const focusFrame = window.requestAnimationFrame(() => {
      (initialFocusRef?.current ?? focusableElements(dialog)[0] ?? dialog).focus();
    });

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        closeRef.current();
        return;
      }
      if (event.key !== "Tab") return;

      const focusable = focusableElements(dialog);
      if (!focusable.length) {
        event.preventDefault();
        dialog.focus();
        return;
      }

      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      const active = document.activeElement;
      if (!dialog.contains(active)) {
        event.preventDefault();
        (event.shiftKey ? last : first).focus();
      } else if (event.shiftKey && active === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && active === last) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", handleKeyDown, true);
    return () => {
      window.cancelAnimationFrame(focusFrame);
      document.removeEventListener("keydown", handleKeyDown, true);
      document.body.style.overflow = previousOverflow;
      for (const { element, wasInert } of backgroundRegions) {
        if (!wasInert) element.removeAttribute("inert");
      }
      window.requestAnimationFrame(() => {
        if (restoreFocusRef?.current !== false && returnTarget?.isConnected) returnTarget.focus();
      });
    };
  }, [dialogRef, initialFocusRef, open, restoreFocusRef, returnFocusRef]);
}
