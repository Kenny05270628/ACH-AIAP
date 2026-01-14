import * as React from "react";

const Button = React.forwardRef(
  ({ className, variant = 'default', size = 'default', ...props }, ref) => {
    // 基础按钮样式
    const baseStyle = "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none";
    
    // 变体样式
    const variantStyles = {
      default: "bg-primary text-white hover:bg-primary/90 focus:ring-primary",
      secondary: "bg-gray-100 text-gray-700 hover:bg-gray-200 focus:ring-gray-300",
      outline: "border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 focus:ring-primary",
      ghost: "bg-transparent text-gray-700 hover:bg-gray-100 focus:ring-gray-200",
      link: "bg-transparent text-primary underline-offset-4 hover:underline",
      destructive: "bg-red-500 text-white hover:bg-red-600 focus:ring-red-500",
    };
    
    // 尺寸样式
    const sizeStyles = {
      default: "h-10 px-4 py-2",
      sm: "h-9 rounded-md px-3",
      lg: "h-11 rounded-md px-8",
      icon: "h-10 w-10",
    };
    
    // 组合所有样式
    const buttonClasses = `${baseStyle} ${variantStyles[variant]} ${sizeStyles[size]} ${className || ''}`;
    
    return (
      <button
        className={buttonClasses}
        ref={ref}
        {...props}
      />
    );
  }
);

Button.displayName = "Button";

export { Button };