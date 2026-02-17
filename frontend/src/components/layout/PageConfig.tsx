import { useEffect } from "react";
import type { NodeComponentProps } from "../../registry/registry";

export const PageConfig: React.FC<NodeComponentProps> = ({ props }) => {
  const { pageTitle, pageIcon, layout, initialSidebarState } = props;

  useEffect(() => {
    // Update document title
    if (pageTitle) {
      document.title = pageTitle;
    }

    // Update favicon if pageIcon is provided
    if (pageIcon) {
      const link = document.querySelector("link[rel~='icon']") as HTMLLinkElement;
      if (link) {
        // If it's an emoji, create a data URL
        if (pageIcon.length <= 2) {
          const canvas = document.createElement("canvas");
          canvas.width = 32;
          canvas.height = 32;
          const ctx = canvas.getContext("2d");
          if (ctx) {
            ctx.font = "28px serif";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText(pageIcon, 16, 18);
            link.href = canvas.toDataURL();
          }
        } else {
          // Assume it's a URL
          link.href = pageIcon;
        }
      }
    }

    // Apply layout class to body
    if (layout === "wide") {
      document.body.classList.add("layout-wide");
      document.body.classList.remove("layout-centered");
    } else {
      document.body.classList.add("layout-centered");
      document.body.classList.remove("layout-wide");
    }

    // Store sidebar state preference
    if (initialSidebarState) {
      document.body.dataset.sidebarState = initialSidebarState;
    }
  }, [pageTitle, pageIcon, layout, initialSidebarState]);

  // This component doesn't render anything visible
  return null;
};
