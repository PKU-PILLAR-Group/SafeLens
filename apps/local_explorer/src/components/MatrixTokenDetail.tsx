import type { TokenInfo } from "../types";

interface MatrixTokenDetailProps {
  tokens: TokenInfo[];
  tokenIndex: number;
  roleLabel?: string;
  fallbackText?: string;
}

export function MatrixTokenDetail({
  tokens,
  tokenIndex,
  roleLabel = "token",
  fallbackText
}: MatrixTokenDetailProps) {
  const token = tokens.find((item) => item.index === tokenIndex);
  const position = token?.index ?? tokenIndex;
  const text = tokenDisplayText(token?.text ?? fallbackText);
  const tokenId = token?.tokenId;
  return (
    <span className="matrix-token-detail">
      <b title={token ? matrixTokenTitle(token, roleLabel) : `${roleLabel} position ${position}`}>
        {text}
      </b>
      {roleLabel} position {position} · id {tokenId ?? "unknown"}
    </span>
  );
}

export function matrixTokenTitle(token: TokenInfo, roleLabel = "token") {
  return `${roleLabel} position ${token.index} · id ${token.tokenId} · text ${tokenDisplayText(token.text)}`;
}

function tokenDisplayText(value: string | undefined) {
  return value?.length ? value : "␠";
}
