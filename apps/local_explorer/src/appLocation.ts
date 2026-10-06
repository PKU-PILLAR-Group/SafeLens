// Capture the mount path before SPA navigation changes the current URL.
// Named screens live immediately below this path, including behind a proxy.
export const APP_BASE_PATH = window.location.pathname
  .replace(/\/(?:explorer|dataset-test|index\.html)\/?$/, "/")
  .replace(/\/?$/, "/");

export function appScreenPath(screen: string = ""): string {
  return `${APP_BASE_PATH}${screen}`;
}
