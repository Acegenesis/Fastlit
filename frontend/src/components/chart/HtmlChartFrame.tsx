import React, { useEffect, useMemo, useState } from "react";

interface HtmlChartFrameProps {
  html?: string;
  height: number;
  title: string;
  emptyMessage: string;
  sandbox?: string;
}

export const HtmlChartFrame: React.FC<HtmlChartFrameProps> = ({
  html,
  height,
  title,
  emptyMessage,
  sandbox = "allow-scripts",
}) => {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    setIsLoaded(false);
    if (!html) {
      setBlobUrl(null);
      return;
    }

    try {
      const url = URL.createObjectURL(new Blob([html], { type: "text/html" }));
      setBlobUrl(url);
      return () => URL.revokeObjectURL(url);
    } catch {
      setBlobUrl(null);
    }
  }, [html]);

  const iframeKey = useMemo(
    () => `${title}:${html?.length ?? 0}:${blobUrl ?? "srcdoc"}`,
    [blobUrl, html, title]
  );

  if (!html) {
    return (
      <div className="mb-4 p-4 text-sm text-gray-500 bg-gray-50 rounded-lg border">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className="mb-4 relative w-full rounded-lg overflow-hidden border border-gray-200">
      {!isLoaded && (
        <div
          className="absolute inset-0 z-10 flex items-center justify-center bg-muted/20"
          style={{ height }}
        >
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
            <span>Loading chart...</span>
          </div>
        </div>
      )}
      <iframe
        key={iframeKey}
        src={blobUrl ?? undefined}
        srcDoc={blobUrl ? undefined : html}
        style={{ width: "100%", height, border: "none", display: "block" }}
        sandbox={sandbox}
        loading="lazy"
        onLoad={() => setIsLoaded(true)}
        title={title}
      />
    </div>
  );
};
