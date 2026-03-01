export function normalizeGridColumnType(type: string | null | undefined): string {
  const normalized = String(type ?? "text").trim().toLowerCase();

  switch (normalized) {
    case "":
    case "default":
    case "string":
    case "str":
    case "text":
      return "text";
    case "bool":
    case "boolean":
    case "checkbox":
      return "checkbox";
    case "select":
    case "selectbox":
      return "selectbox";
    case "url":
    case "href":
    case "uri":
    case "link":
    case "link_button":
      return "link";
    case "img":
    case "image":
    case "image_url":
      return "image";
    case "object":
      return "json";
    default:
      return normalized;
  }
}
