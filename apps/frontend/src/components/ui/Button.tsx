import React from 'react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary';
}

export const Button = ({ variant = 'primary', style, ...props }: ButtonProps) => {
  const baseStyle: React.CSSProperties = {
    padding: '8px 16px',
    borderRadius: '4px',
    border: 'none',
    cursor: 'pointer',
    fontWeight: 'bold',
  };

  const variantStyles: Record<string, React.CSSProperties> = {
    primary: {
      backgroundColor: '#0070f3',
      color: 'white',
    },
    secondary: {
      backgroundColor: '#eaeaea',
      color: '#333',
    },
  };

  return (
    <button
      style={{ ...baseStyle, ...variantStyles[variant], ...style }}
      {...props}
    />
  );
};
