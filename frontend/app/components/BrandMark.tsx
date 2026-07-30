type BrandMarkProps = {
  className?: string;
};

export default function BrandMark({ className }: BrandMarkProps) {
  return (
    <svg
      aria-hidden="true"
      className={className}
      focusable="false"
      viewBox="0 0 48 48"
    >
      <rect width="48" height="48" rx="12" fill="#1f3325" />
      <path
        d="M9.5 24.5 24 11l14.5 13.5"
        fill="none"
        stroke="#f2c174"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="3.5"
      />
      <path
        d="M14.5 23.5V37h19V23.5"
        fill="#fff7e8"
        stroke="#fff7e8"
        strokeLinejoin="round"
        strokeWidth="2"
      />
      <path
        d="M20 37v-9h8v9M17.5 28h2M28.5 28h2M17.5 32h2M28.5 32h2"
        fill="none"
        stroke="#1f3325"
        strokeLinecap="round"
        strokeWidth="2"
      />
    </svg>
  );
}
