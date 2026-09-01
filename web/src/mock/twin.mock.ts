/** Twin module mock fixtures */

export const recoveryChart = Array.from({ length: 20 }, (_, i) =>
  +(5 + (70 - 5) * (1 - Math.exp(-0.15 * i))).toFixed(2)
);
