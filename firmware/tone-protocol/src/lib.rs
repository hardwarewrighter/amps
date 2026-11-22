#![no_std]

pub const SAMPLE_RATE: u32 = 32_000;
pub const MIN_HZ: u32 = 20;
pub const MAX_HZ: u32 = 5_000;
pub const MAX_LINE: usize = 48;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Command {
    Start,
    Stop,
    Frequency(u32),
    Status,
}

pub fn parse(line: &[u8]) -> Result<Command, &'static str> {
    let text = core::str::from_utf8(line).map_err(|_| "ERR encoding\n")?;
    let mut words = text.split_ascii_whitespace();
    let verb = words.next().ok_or("ERR empty command\n")?;
    let cmd = if verb.eq_ignore_ascii_case("START") {
        Command::Start
    } else if verb.eq_ignore_ascii_case("STOP") {
        Command::Stop
    } else if verb.eq_ignore_ascii_case("STATUS") {
        Command::Status
    } else if verb.eq_ignore_ascii_case("FREQ") {
        let hz = words
            .next()
            .and_then(|s| s.parse::<u32>().ok())
            .filter(|n| (MIN_HZ..=MAX_HZ).contains(n))
            .ok_or("ERR frequency must be integer 20..5000 Hz\n")?;
        Command::Frequency(hz)
    } else {
        return Err("ERR unknown command\n");
    };
    if words.next().is_some() {
        return Err("ERR extra arguments\n");
    }
    Ok(cmd)
}

pub struct Lines {
    data: [u8; MAX_LINE],
    len: usize,
    overflow: bool,
}
impl Default for Lines {
    fn default() -> Self {
        Self::new()
    }
}
impl Lines {
    pub const fn new() -> Self {
        Self {
            data: [0; MAX_LINE],
            len: 0,
            overflow: false,
        }
    }
    pub fn push(&mut self, byte: u8) -> Option<Result<Command, &'static str>> {
        match byte {
            b'\r' => None,
            b'\n' => {
                let result = if self.overflow {
                    Err("ERR line too long\n")
                } else {
                    parse(&self.data[..self.len])
                };
                self.len = 0;
                self.overflow = false;
                Some(result)
            }
            _ => {
                if self.len == MAX_LINE {
                    self.overflow = true;
                } else {
                    self.data[self.len] = byte;
                    self.len += 1;
                }
                None
            }
        }
    }
}

const WAVE: [u16; 32] = [
    511, 611, 707, 795, 873, 936, 984, 1013, 1023, 1013, 984, 936, 873, 795, 707, 611, 511, 411,
    315, 227, 149, 86, 38, 9, 0, 9, 38, 86, 149, 227, 315, 411,
];

pub struct Synth {
    pub running: bool,
    pub hz: u32,
    phase: u32,
    step: u32,
}
impl Default for Synth {
    fn default() -> Self {
        Self::new()
    }
}
impl Synth {
    pub const fn new() -> Self {
        Self {
            running: false,
            hz: 440,
            phase: 0,
            step: ((440u64 << 32) / SAMPLE_RATE as u64) as u32,
        }
    }
    pub fn apply(&mut self, cmd: Command) {
        match cmd {
            Command::Start => {
                self.phase = 0;
                self.running = true;
            }
            Command::Stop => self.running = false,
            Command::Frequency(hz) => {
                self.hz = hz;
                self.step = ((hz as u64 * (1u64 << 32) + SAMPLE_RATE as u64 / 2)
                    / SAMPLE_RATE as u64) as u32;
            }
            Command::Status => {}
        }
    }
    pub fn sample(&mut self) -> u16 {
        if !self.running {
            return 512;
        }
        let value = WAVE[(self.phase >> 27) as usize];
        self.phase = self.phase.wrapping_add(self.step);
        value
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn commands_and_validation() {
        assert_eq!(parse(b"freq 880"), Ok(Command::Frequency(880)));
        assert_eq!(parse(b" START "), Ok(Command::Start));
        for bad in [
            b"FREQ 0".as_slice(),
            b"FREQ 5001",
            b"FREQ -1",
            b"FREQ 440.5",
            b"FREQ 999999999999999",
            b"STOP extra",
            b"START STOP",
            b"",
            b"BOOP",
            b"\xff",
        ] {
            assert!(parse(bad).is_err(), "{:?}", bad);
        }
    }
    #[test]
    fn fragmented_crlf_multiple_and_overflow() {
        let mut lines = Lines::new();
        for b in b"FR" {
            assert!(lines.push(*b).is_none());
        }
        for b in b"EQ 440\r" {
            assert!(lines.push(*b).is_none());
        }
        assert_eq!(lines.push(b'\n'), Some(Ok(Command::Frequency(440))));
        for _ in 0..MAX_LINE + 1 {
            lines.push(b'X');
        }
        assert!(lines.push(b'\n').unwrap().is_err());
        for b in b"STOP" {
            lines.push(*b);
        }
        assert_eq!(lines.push(b'\n'), Some(Ok(Command::Stop)));
    }
    #[test]
    fn silence_start_frequency_and_stop() {
        let mut s = Synth::new();
        assert_eq!(s.sample(), 512);
        assert_eq!(s.hz, 440);
        s.apply(Command::Frequency(1000)); // exactly one table position per sample
        s.apply(Command::Start);
        for _ in 0..5 {
            for expected in WAVE {
                assert_eq!(s.sample(), expected);
            }
        }
        s.apply(Command::Stop);
        for _ in 0..100 {
            assert_eq!(s.sample(), 512);
        }
        s.apply(Command::Frequency(880));
        assert!(!s.running);
    }
}
