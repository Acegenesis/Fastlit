import * as React from "react";

import { cn } from "@/lib/utils";

const AvatarContext = React.createContext<{
  imageLoaded: boolean;
  setImageLoaded: (loaded: boolean) => void;
}>({
  imageLoaded: false,
  setImageLoaded: () => undefined,
});

const Avatar = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, children, ...props }, ref) => {
    const [imageLoaded, setImageLoaded] = React.useState(false);

    return (
      <AvatarContext.Provider value={{ imageLoaded, setImageLoaded }}>
        <div
          ref={ref}
          className={cn(
            "relative flex h-10 w-10 shrink-0 overflow-hidden rounded-full",
            className
          )}
          {...props}
        >
          {children}
        </div>
      </AvatarContext.Provider>
    );
  }
);
Avatar.displayName = "Avatar";

const AvatarImage = React.forwardRef<
  HTMLImageElement,
  React.ImgHTMLAttributes<HTMLImageElement>
>(({ className, onLoad, onError, ...props }, ref) => {
  const { setImageLoaded } = React.useContext(AvatarContext);

  return (
    <img
      ref={ref}
      className={cn("aspect-square h-full w-full object-cover", className)}
      onLoad={(event) => {
        setImageLoaded(true);
        onLoad?.(event);
      }}
      onError={(event) => {
        setImageLoaded(false);
        onError?.(event);
      }}
      {...props}
    />
  );
});
AvatarImage.displayName = "AvatarImage";

const AvatarFallback = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => {
    const { imageLoaded } = React.useContext(AvatarContext);
    if (imageLoaded) return null;
    return (
      <div
        ref={ref}
        className={cn(
          "flex h-full w-full items-center justify-center rounded-full bg-muted",
          className
        )}
        {...props}
      />
    );
  }
);
AvatarFallback.displayName = "AvatarFallback";

export { Avatar, AvatarImage, AvatarFallback };
