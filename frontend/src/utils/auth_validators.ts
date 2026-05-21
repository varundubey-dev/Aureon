const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const USERNAME_REGEX = /^(?!.*__)[a-zA-Z0-9_]{3,20}$/;

const NAME_REGEX = /^[a-zA-Z]+(?: [a-zA-Z]+)*$/;

const PASSWORD_REGEX =
  /^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*])[A-Za-z\d!@#$%^&*]{6,}$/;

export function validateName(name: string): string {
  const trimmed = name.trim();

  if (!trimmed) {
    return "Name is required";
  }

  if (trimmed.length < 2) {
    return "Name must be at least 2 characters";
  }

  if (!NAME_REGEX.test(trimmed)) {
    return "Name can only contain letters and spaces";
  }

  return "";
}

export function validateEmail(email: string): string {
  const trimmed = email.trim();

  if (!trimmed) {
    return "Email is required";
  }

  if (!EMAIL_REGEX.test(trimmed)) {
    return "Enter a valid email";
  }

  return "";
}

export function validateUsername(username: string): string {
  const trimmed = username.trim();

  if (!trimmed) {
    return "Username is required";
  }

  if (trimmed.length < 3) {
    return "Username must be at least 3 characters";
  }

  if (trimmed.length > 20) {
    return "Username cannot exceed 20 characters";
  }

  if (!USERNAME_REGEX.test(trimmed)) {
    return "Only letters, numbers, and underscores allowed";
  }

  if (trimmed.startsWith("_") || trimmed.endsWith("_")) {
    return "Username cannot start or end with underscore";
  }

  return "";
}

export function validatePassword(password: string): string {
  if (!password) {
    return "Password is required";
  }

  if (password.length < 6) {
    return "Password must be at least 6 characters";
  }

  if (!PASSWORD_REGEX.test(password)) {
    return "Password must contain 1 uppercase letter, 1 number, and 1 symbol";
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
