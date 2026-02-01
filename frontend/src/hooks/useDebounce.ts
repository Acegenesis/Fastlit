import { useRef, useCallback } from "react";

/**
 * Returns a debounced version of the callback.
 * The callback will only fire after `delay` ms of inactivity.
 */
export function useDebouncedCallback<T extends (...args: any[]) => void>(
  callback: T,
  delay: number
): T {
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  return useCallback(
    ((...args: any[]) => {
      if (timer.current) clearTimeout(timer.current);
      timer.current = setTimeout(() => callback(...args), delay);
    }) as T,
    [callback, delay]
  );
}
