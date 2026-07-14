declare module "ml-hclust" {
  export type AgglomerationMethod =
    | "single"
    | "complete"
    | "average"
    | "upgma"
    | "wpgma"
    | "median"
    | "wpgmc"
    | "centroid"
    | "upgmc"
    | "ward"
    | "ward2";

  export class Cluster {
    children: Cluster[];
    height: number;
    size: number;
    index: number;
    isLeaf: boolean;
    cut(threshold: number): Cluster[];
    group(groups: number): Cluster;
    traverse(callback: (cluster: Cluster) => void): void;
    indices(): number[];
  }

  export function agnes<T>(
    data: T[],
    options?: {
      distanceFunction?: (left: T, right: T) => number;
      method?: AgglomerationMethod;
      isDistanceMatrix?: boolean;
    }
  ): Cluster;
}
