import { agnes } from "ml-hclust";

interface ClusterRequest {
  id: number;
  profiles: number[][];
  similarityThreshold: number;
}

interface ClusterResult {
  id: number;
  clusters: Array<{
    indices: number[];
    height: number;
  }>;
}

interface ClusterFailure {
  id: number;
  error: string;
}

self.addEventListener("message", (event: MessageEvent<ClusterRequest>) => {
  const { id, profiles, similarityThreshold } = event.data;
  try {
    if (profiles.length === 0) {
      self.postMessage({ id, clusters: [] } satisfies ClusterResult);
      return;
    }
    if (profiles.length === 1) {
      self.postMessage({
        id,
        clusters: [{ indices: [0], height: 0 }]
      } satisfies ClusterResult);
      return;
    }
    const tree = agnes(profiles, {
      method: "average",
      distanceFunction: absolutePearsonDistance
    });
    const clusters = tree
      .cut(Math.max(0, Math.min(1, 1 - similarityThreshold)) + 1e-12)
      .map((cluster) => ({
        indices: cluster.indices(),
        height: cluster.height
      }));
    self.postMessage({ id, clusters } satisfies ClusterResult);
  } catch (error) {
    self.postMessage({
      id,
      error: error instanceof Error ? error.message : "MLP clustering failed."
    } satisfies ClusterFailure);
  }
});

function absolutePearsonDistance(left: number[], right: number[]) {
  const correlation = pearsonCorrelation(left, right);
  return 1 - Math.abs(correlation);
}

function pearsonCorrelation(left: number[], right: number[]) {
  const length = Math.min(left.length, right.length);
  if (length === 0) return 0;
  let leftMean = 0;
  let rightMean = 0;
  for (let index = 0; index < length; index += 1) {
    leftMean += finite(left[index]);
    rightMean += finite(right[index]);
  }
  leftMean /= length;
  rightMean /= length;
  let numerator = 0;
  let leftSquare = 0;
  let rightSquare = 0;
  for (let index = 0; index < length; index += 1) {
    const leftCentered = finite(left[index]) - leftMean;
    const rightCentered = finite(right[index]) - rightMean;
    numerator += leftCentered * rightCentered;
    leftSquare += leftCentered * leftCentered;
    rightSquare += rightCentered * rightCentered;
  }
  const denominator = Math.sqrt(leftSquare * rightSquare);
  if (denominator <= 1e-12) return 0;
  return Math.max(-1, Math.min(1, numerator / denominator));
}

function finite(value: number | undefined) {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}
