/**
 * Fullscreen API utility helper with cross-browser and vendor-prefix support.
 */

export function isFullscreen(): boolean {
  if (typeof document === 'undefined') return false;
  const doc = document as any;
  return Boolean(
    doc.fullscreenElement ||
    doc.webkitFullscreenElement ||
    doc.mozFullScreenElement ||
    doc.msFullscreenElement
  );
}

export async function enterFullscreen(): Promise<boolean> {
  if (typeof document === 'undefined') return false;
  try {
    const elem = document.documentElement as any;
    if (elem.requestFullscreen) {
      await elem.requestFullscreen();
      return true;
    } else if (elem.webkitRequestFullscreen) {
      await elem.webkitRequestFullscreen();
      return true;
    } else if (elem.mozRequestFullScreen) {
      await elem.mozRequestFullScreen();
      return true;
    } else if (elem.msRequestFullscreen) {
      await elem.msRequestFullscreen();
      return true;
    }
  } catch (err) {
    console.warn('Unable to enter fullscreen:', err);
  }
  return false;
}

export async function exitFullscreen(): Promise<boolean> {
  if (typeof document === 'undefined') return false;
  try {
    const doc = document as any;
    if (doc.exitFullscreen) {
      await doc.exitFullscreen();
      return true;
    } else if (doc.webkitExitFullscreen) {
      await doc.webkitExitFullscreen();
      return true;
    } else if (doc.mozCancelFullScreen) {
      await doc.mozCancelFullScreen();
      return true;
    } else if (doc.msExitFullscreen) {
      await doc.msExitFullscreen();
      return true;
    }
  } catch (err) {
    console.warn('Unable to exit fullscreen:', err);
  }
  return false;
}

export async function toggleFullscreen(): Promise<boolean> {
  if (isFullscreen()) {
    return !(await exitFullscreen());
  } else {
    return await enterFullscreen();
  }
}

export function subscribeToFullscreen(callback: (fullscreen: boolean) => void): () => void {
  if (typeof document === 'undefined') return () => {};

  const handler = () => {
    callback(isFullscreen());
  };

  document.addEventListener('fullscreenchange', handler);
  document.addEventListener('webkitfullscreenchange', handler);
  document.addEventListener('mozfullscreenchange', handler);
  document.addEventListener('MSFullscreenChange', handler);

  return () => {
    document.removeEventListener('fullscreenchange', handler);
    document.removeEventListener('webkitfullscreenchange', handler);
    document.removeEventListener('mozfullscreenchange', handler);
    document.removeEventListener('MSFullscreenChange', handler);
  };
}
