import React, {
  createContext,
  useContext,
  type ComponentType
} from "react";

export const LazyRetryGenerationContext = createContext(0);

declare global {
  interface Window {
    __SAFELENS_TEST_LAZY_TIMEOUT_MS__?: number;
  }
}

const DEFAULT_LAZY_TIMEOUT_MS = 12_000;

export function retryableLazy<
  // The loader's concrete module type is retained through ReturnType below.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  Loader extends () => Promise<any>,
  ExportName extends keyof Awaited<ReturnType<Loader>>
>(loader: Loader, exportName: ExportName) {
  type LoadedModule = Awaited<ReturnType<Loader>>;
  // ComponentType<any> is used only to extract the selected module export.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  type LoadedComponent = Extract<LoadedModule[ExportName], ComponentType<any>>;
  type Props = React.ComponentProps<LoadedComponent>;
  const components = new Map<number, React.LazyExoticComponent<LoadedComponent>>();

  function loadModule() {
    const timeoutMs = import.meta.env.DEV
      ? window.__SAFELENS_TEST_LAZY_TIMEOUT_MS__ ?? DEFAULT_LAZY_TIMEOUT_MS
      : DEFAULT_LAZY_TIMEOUT_MS;
    return new Promise<LoadedModule>((resolve, reject) => {
      const timeout = window.setTimeout(() => {
        reject(new Error(`Lazy module ${String(exportName)} timed out after ${timeoutMs}ms`));
      }, timeoutMs);
      void loader().then(
        (module) => {
          window.clearTimeout(timeout);
          resolve(module);
        },
        (error) => {
          window.clearTimeout(timeout);
          reject(error);
        }
      );
    });
  }

  function componentForGeneration(generation: number) {
    const current = components.get(generation);
    if (current) return current;
    const created = React.lazy(() => loadModule().then((module) => ({
        default: module[exportName] as LoadedComponent
      })));
    components.set(generation, created);
    return created;
  }

  function RetryableLazyComponent(props: Props) {
    const generation = useContext(LazyRetryGenerationContext);
    const LazyComponent = componentForGeneration(generation);
    return React.createElement(
      LazyComponent as React.ComponentType<Props>,
      // React's createElement overload cannot express the extracted generic props.
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      props as any
    );
  }

  RetryableLazyComponent.displayName = "RetryableLazyComponent";
  return RetryableLazyComponent;
}
