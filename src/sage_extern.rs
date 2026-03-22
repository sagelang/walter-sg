//! Walter extern functions — Rust implementations for stdlib gaps.
//!
//! Provides time utilities (sleep, now, date decomposition) and JSON escaping
//! that Sage's stdlib doesn't yet cover. Following Ward's pattern: plain pub fn,
//! owned String parameters, no FFI boilerplate.

/// Get current UTC time as milliseconds since Unix epoch.
pub fn now_utc() -> i64 {
    chrono::Utc::now().timestamp_millis()
}

/// Sleep for the given number of milliseconds.
/// In a tokio context this yields the task; here we block the thread
/// since sage-runtime drives each agent on its own task.
pub fn sleep_ms(ms: i64) {
    if ms > 0 {
        std::thread::sleep(std::time::Duration::from_millis(ms as u64));
    }
}

/// Decompose a UTC epoch-ms timestamp into (year, month, day) as a comma-separated string.
/// Returns "YYYY,MM,DD" — parsed back in Sage.
pub fn date_from_utc_ms(ms: i64) -> String {
    use chrono::{TimeZone, Datelike};
    let dt = chrono::Utc.timestamp_millis_opt(ms).unwrap();
    format!("{},{},{}", dt.year(), dt.month(), dt.day())
}

/// Get current date as "YYYY,MM,DD" string (convenience wrapper).
pub fn today_utc() -> String {
    date_from_utc_ms(now_utc())
}

/// Extract the month (1-12) from a "YYYY,MM,DD" date string.
pub fn date_month(date_str: String) -> i64 {
    date_str
        .split(',')
        .nth(1)
        .and_then(|s| s.parse::<i64>().ok())
        .unwrap_or(1)
}

/// Extract the day (1-31) from a "YYYY,MM,DD" date string.
pub fn date_day(date_str: String) -> i64 {
    date_str
        .split(',')
        .nth(2)
        .and_then(|s| s.parse::<i64>().ok())
        .unwrap_or(1)
}

/// Escape a string for safe embedding in a JSON value.
/// Handles quotes, backslashes, newlines, tabs, and control characters.
pub fn json_escape(s: String) -> String {
    let mut out = String::with_capacity(s.len() + 16);
    for c in s.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if (c as u32) < 0x20 => {
                out.push_str(&format!("\\u{:04x}", c as u32));
            }
            c => out.push(c),
        }
    }
    out
}

/// Compute milliseconds until the next occurrence of HH:MM UTC.
/// If the time has already passed today, returns the delay until tomorrow.
pub fn ms_until_next(hour: i64, minute: i64) -> i64 {
    use chrono::{Timelike, Utc};
    let now = Utc::now();
    let now_secs = (now.hour() as i64) * 3600 + (now.minute() as i64) * 60 + (now.second() as i64);
    let target_secs = hour * 3600 + minute * 60;
    let delta_secs = if now_secs < target_secs {
        target_secs - now_secs
    } else {
        86400 - now_secs + target_secs
    };
    delta_secs * 1000
}

/// Parse an integer from a string, returning 0 on failure.
pub fn parse_int_safe(s: String) -> i64 {
    s.trim().parse::<i64>().unwrap_or(0)
}

/// Read an environment variable, returning empty string if not set.
pub fn env_or_default(key: String, default: String) -> String {
    std::env::var(&key).unwrap_or(default)
}

/// Truncate a string to fit Discord's 2000-character message limit.
/// If truncated, appends "..." to indicate continuation.
pub fn discord_truncate(s: String, max_len: i64) -> String {
    let max = max_len as usize;
    if s.len() <= max {
        s
    } else {
        let truncated = &s[..max.saturating_sub(3)];
        format!("{}...", truncated)
    }
}
