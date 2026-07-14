export function scrollElementInlineCenter(container: HTMLElement, element: HTMLElement) {
  const centeredLeft = element.offsetLeft + element.offsetWidth / 2 - container.clientWidth / 2;
  const maximumLeft = Math.max(0, container.scrollWidth - container.clientWidth);
  container.scrollLeft = Math.min(maximumLeft, Math.max(0, centeredLeft));
}
