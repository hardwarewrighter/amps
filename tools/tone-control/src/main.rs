use std::{
    env,
    fs::OpenOptions,
    io::{self, Read, Write},
    os::unix::fs::OpenOptionsExt,
    process::{self, Command},
    thread,
    time::{Duration, Instant},
};

const USAGE: &str = "Usage: tone-control --port /dev/ttyACM0 start|stop|status|frequency HZ\n\
                     Frequency: integer 20..5000 Hz. Firmware boots stopped at 440 Hz.";

fn main() {
    if let Err(e) = run() {
        eprintln!("tone-control: {e}");
        process::exit(1);
    }
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().skip(1).collect();
    if args == ["--help"] || args == ["-h"] {
        println!("{USAGE}");
        return Ok(());
    }
    if args.len() < 3 || args[0] != "--port" {
        return Err(USAGE.into());
    }
    let port = &args[1];
    let request = match args[2].as_str() {
        "start" if args.len() == 3 => "START\n".to_owned(),
        "stop" if args.len() == 3 => "STOP\n".to_owned(),
        "status" if args.len() == 3 => "STATUS\n".to_owned(),
        "frequency" | "freq" if args.len() == 4 => format!("FREQ {}\n", args[3]),
        _ => return Err(USAGE.into()),
    };
    tone_protocol::parse(request.trim().as_bytes()).map_err(|e| e.trim())?;
    // Linux termios setup through stty keeps this controller free of external crates.
    let configured = Command::new("stty")
        .args([
            "-F", port, "115200", "raw", "-echo", "-hupcl", "clocal", "min", "0", "time", "0",
        ])
        .status()?;
    if !configured.success() {
        return Err("cannot configure serial port; check device and permissions".into());
    }
    // Linux O_NONBLOCK | O_NOCTTY. Opening a USB CDC port does not reset this firmware.
    let mut serial = OpenOptions::new()
        .read(true)
        .write(true)
        .custom_flags(0x800 | 0x100)
        .open(port)?;
    let deadline = Instant::now() + Duration::from_secs(5);
    let mut sent = 0;
    while sent < request.len() {
        match serial.write(&request.as_bytes()[sent..]) {
            Ok(0) => thread::sleep(Duration::from_millis(5)),
            Ok(n) => sent += n,
            Err(e)
                if matches!(
                    e.kind(),
                    io::ErrorKind::WouldBlock | io::ErrorKind::Interrupted
                ) =>
            {
                thread::sleep(Duration::from_millis(5))
            }
            Err(e) => return Err(e.into()),
        }
        if Instant::now() >= deadline {
            return Err("timed out sending command".into());
        }
    }
    let mut response = Vec::new();
    loop {
        let mut buf = [0u8; 128];
        match serial.read(&mut buf) {
            Ok(n) => {
                for &b in &buf[..n] {
                    if b == b'\n' {
                        let line = String::from_utf8(response)?;
                        if line.starts_with("OK ") {
                            println!("{line}");
                            return Ok(());
                        }
                        return Err(format!("device replied: {line}").into());
                    }
                    response.push(b);
                    if response.len() > 256 {
                        return Err("invalid/oversized device response".into());
                    }
                }
            }
            Err(e)
                if matches!(
                    e.kind(),
                    io::ErrorKind::WouldBlock | io::ErrorKind::Interrupted
                ) =>
            {
                ()
            }
            Err(e) => return Err(e.into()),
        }
        if Instant::now() >= deadline {
            return Err("no firmware acknowledgment within 5 seconds; check port and flash dac-usb firmware".into());
        }
        thread::sleep(Duration::from_millis(5));
    }
}
