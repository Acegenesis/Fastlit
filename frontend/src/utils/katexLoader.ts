let katexModulePromise: Promise<typeof import("katex")> | null = null;
let katexCssPromise: Promise<unknown> | null = null;

export async function loadKatex(): Promise<typeof import("katex")> {
  if (!katexCssPromise) {
    katexCssPromise = import("katex/dist/katex.min.css");
  }
  if (!katexModulePromise) {
    katexModulePromise = import("katex");
  }

  await katexCssPromise;
  return katexModulePromise;
}
