import React from "react";
import type { NodeComponentProps } from "../../registry/registry";

/**
 * StaticHtml — renders either:
 *  - a sandboxed HTML string (st.components.v1.html)
 *  - an external URL in a plain iframe (st.components.v1.iframe)
 *
 * Security:
 *  - srcDoc iframes use sandbox="allow-scripts" so scripts run but cannot
 *    access the parent page's cookies, DOM, or localStorage.
 *  - src iframes have no extra sandbox (the external site controls its own
 *    security headers).
 */
export const StaticHtml: React.FC<NodeComponentProps> = ({ props }) => {
  const {
    html,
    src,
    height = 150,
    scrolling = false,
  } = props as {
    html?: string;
    src?: string;
    height?: number;
    scrolling?: boolean;
  };

  const commonStyle: React.CSSProperties = {
    width: "100%",
    height: `${height}px`,
    border: "none",
    display: "block",
    overflow: scrolling ? "auto" : "hidden",
  };

  const scrollAttr = scrolling ? "yes" : "no";

  // Key forces iframe remount when content changes so srcDoc/src updates
  // are always applied — browsers don't reliably reload iframes on attr change.
  const iframeKey = src ?? html ?? "";

  if (src) {
    return (
      <iframe
        key={iframeKey}
        src={src}
        style={commonStyle}
        scrolling={scrollAttr}
        title="fastlit-iframe"
      />
    );
  }

  // Sandboxed HTML string — allow-scripts only (no same-origin access)
  return (
    <iframe
      key={iframeKey}
      srcDoc={html ?? ""}
      sandbox="allow-scripts"
      style={commonStyle}
      scrolling={scrollAttr}
      title="fastlit-html"
    />
  );
};
