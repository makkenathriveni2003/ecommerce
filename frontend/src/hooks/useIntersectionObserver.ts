import { useCallback, useEffect, useState } from "react"

export function useIntersectionObserver(
  onIntersect: () => void,
  enabled = true,
): (node: HTMLDivElement | null) => void {
  const [target, setTarget] = useState<HTMLDivElement | null>(null)
  const ref = useCallback((node: HTMLDivElement | null) => setTarget(node), [])

  useEffect(() => {
    if (!enabled || !target || !("IntersectionObserver" in window)) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry?.isIntersecting) onIntersect()
      },
      { rootMargin: "240px" },
    )

    observer.observe(target)
    return () => observer.disconnect()
  }, [enabled, onIntersect, target])

  return ref
}
