/** Public service module mock fixtures */

export const announcements = [
  { id: 1, title: "供热季缴费通道已开启", content: "2026-2027 采暖季线上缴费已开放，请提前办理。", publishedAt: "2026-09-15 09:00:00" },
  { id: 2, title: "城北片区检修停暖通知", content: "城北一次网检修，预计停暖 6 小时，请做好准备。", publishedAt: "2026-09-10 14:30:00" },
];

export const serviceRequests = [
  { id: 1, type: "报修", phone: "138****1234", status: "已受理", createdAt: "2026-09-14 10:12:00" },
  { id: 2, type: "投诉", phone: "139****5678", status: "处理中", createdAt: "2026-09-13 16:40:00" },
];
