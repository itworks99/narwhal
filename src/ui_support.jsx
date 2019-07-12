export const chartColors = [
  '#8E3642',
  '#A42150',
  '#BC3148',
  '#DA1E45',
  '#F5D03E',
  '#7AA543',
  '#6C99D7 ',
  '#CCD3D9',
];

// RFC 5424

export const syslogSeverity = [
  { key: 0, text: 'Emergency', value: 0 },
  { key: 1, text: 'Alert', value: 1 },
  { key: 2, text: 'Critical', value: 2 },
  { key: 3, text: 'Error', value: 3 },
  { key: 4, text: 'Warning', value: 4 },
  { key: 5, text: 'Notice', value: 5 },
  { key: 6, text: 'Informational', value: 6 },
  { key: 7, text: 'Debug', value: 7 },
];

export const syslogFacility = [
  { key: 0, text: 'kern', value: 0 },
  { key: 1, text: 'user', value: 1 },
  { key: 2, text: 'mail', value: 2 },
  { key: 3, text: 'daemon', value: 3 },
  { key: 4, text: 'auth', value: 4 },
  { key: 5, text: 'syslog', value: 5 },
  { key: 6, text: 'lpr', value: 6 },
  { key: 7, text: 'news', value: 7 },
  { key: 8, text: 'uucp', value: 8 },
  { key: 9, text: 'cron', value: 9 },
  { key: 10, text: 'authpriv', value: 10 },
  { key: 11, text: 'ftp', value: 11 },
  { key: 12, text: 'ntp', value: 12 },
  { key: 13, text: 'security', value: 13 },
  { key: 14, text: 'console', value: 14 },
  { key: 15, text: 'solaris-cron', value: 15 },
  { key: 16, text: 'local0', value: 16 },
  { key: 17, text: 'local1', value: 17 },
  { key: 18, text: 'local2', value: 18 },
  { key: 19, text: 'local3', value: 19 },
  { key: 20, text: 'local4', value: 20 },
  { key: 21, text: 'local5', value: 21 },
  { key: 22, text: 'local6', value: 22 },
  { key: 23, text: 'local7', value: 23 },
];

export const refreshOptions = [
  { key: 3, text: '3 seconds', value: 3 },
  { key: 5, text: '5 seconds', value: 5 },
  { key: 10, text: '10 seconds', value: 10 },
  { key: 20, text: '20 seconds', value: 20 },
  { key: 40, text: '40 seconds', value: 40 },
  { key: 60, text: '60 seconds', value: 60 },
];

export const dashboardDefaultTimePeriodOptions = [
  { key: 1, text: '1 hour', value: 1 },
  { key: 4, text: '4 hours', value: 4 },
  { key: 6, text: '6 hours', value: 6 },
  { key: 12, text: '12 hours', value: 12 },
  { key: 24, text: '24 hours', value: 24 },
  { key: 48, text: '48 hours', value: 48 },
];

export const dashboardDefaultZoomOptions = [
  { key: 5, text: '5 minutes', value: 5 },
  { key: 15, text: '15 minutes', value: 15 },
  { key: 30, text: '30 minutes', value: 30 },
  { key: 1, text: '1 hour', value: 60 },
  { key: 3, text: '3 hours', value: 180 },
  { key: 6, text: '6 hours', value: 360 },
];
