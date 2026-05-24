const USERNAME_REGEX =
  /^(?!.*__)(?!.*\.\.)(?!\d+$)[a-zA-Z0-9._]+$/;

export function validateName(name: string): string {
  const trimmed = name.trim();

  if (!trimmed) {
    return "Name is required";
  }

  return "";
}

export function validateEmail(email: string): string {
  const trimmed = email.trim();

  if (!trimmed) {
    return "Email is required";
  }

  if (!trimmed.includes("@")) {
    return "Enter a valid email";
  }

  return "";
}

export function validateUsername(
  username: string,
): string {
  const trimmed = username.trim();

  if (!trimmed) {
    return "Username is required";
  }

  if (trimmed.includes(" ")) {
    return "Username cannot contain spaces";
  }

  if (!USERNAME_REGEX.test(trimmed)) {
    return (
      "Only letters, numbers, dots, and underscores allowed"
    );
  }

  if (
    trimmed.startsWith("_") ||
    trimmed.endsWith("_") ||
    trimmed.startsWith(".") ||
    trimmed.endsWith(".")
  ) {
    return (
      "Username cannot start or end with dot or underscore"
    );
  }

  return "";
}

export function validatePassword(password: string): string {
  if (!password) {
    return "Password is required";
  }

  if (password.length < 8) {
    return "Password must be at least 8 characters";
  }

  if (!/[A-Z]/.test(password)) {
    return "Password must contain an uppercase letter";
  }

  if (!/[a-z]/.test(password)) {
    return "Password must contain a lowercase letter";
  }

  if (!/\d/.test(password)) {
    return "Password must contain a number";
  }

  if (!/[!@#$%^&*]/.test(password)) {
    return "Password must contain a special character";
  }

  return "";
}

export function validateConfirmPassword(
  password: string,
  confirmPassword: string,
): string {
  if (!confirmPassword) {
    return "Please confirm your password";
  }

  if (password !== confirmPassword) {
    return "Passwords do not match";
  }

  return "";
}

export function validateLoginIdentifier(identifier: string): string {
  if (!identifier.trim()) {
    return "Username or email is required";
  }

  return "";
}

export function validateLoginPassword(password: string): string {
  if (!password) {
    return "Password is required";
  }

  return "";
}

export function validateOtp(otp: string): string {
  const trimmed = otp.trim();

  if (!trimmed) {
    return "OTP is required";
  }

  if (!/^\d{6}$/.test(trimmed)) {
    return "OTP must be 6 digits";
  }

  return "";
}

export function debounce<T extends (...args: any[]) => void>(
  callback: T,
  delay = 500,
) {
  let timeoutId: ReturnType<typeof setTimeout>;

  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);

    timeoutId = setTimeout(() => {
      callback(...args);
    }, delay);
  };
}
