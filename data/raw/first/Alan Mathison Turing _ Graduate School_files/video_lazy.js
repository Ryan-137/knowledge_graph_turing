/**
 * @file
 * Prepare lazy-loaded videos.
 */
(function (Drupal, once) {

  let YouTubeJSIncluded = false;
  let VimeoJSIncluded = false;

  window.YouTubeAPIReady = false;
  let VimeoAPIReady = false;

  // Tracks the video src of the most recently clicked YouTube video.
  // Used to know which video we should autoplay after we swap the placeholder
  // with the embed and wait for it to load.
  let LastYouTubeVideoSrcClicked;

  let uniqueId = 0;
  let unique = function() {
    uniqueId++;
    return uniqueId;
  };

  // Executed by the YouTube player ID when the video is ready for API calls.
  let onYouTubePlayerReady = function onYouTubePlayerReady(event) {
    // Autoplay the video after it's ready.
    // Ensure the video this ready event is for is the same as the most
    // recently clicked video first.
    if (LastYouTubeVideoSrcClicked && event.target.g.matches(`[src^="${LastYouTubeVideoSrcClicked}"]`)) {
      LastYouTubeVideoSrcClicked = null;
      event.target.g.dataset.playerInit = true;
      event.target.playVideo();
    }
  };

  // Called on first and subsequent loads.
  window.playLazyYouTube = () => {
    const vids = document.querySelectorAll('.lazy-youtube:not([data-player-init])');
    if (!vids || !LastYouTubeVideoSrcClicked) {
      return;
    }
    vids.forEach((vid) => {
      this.player = new YT.Player(vid.getAttribute('id'), {
        playerVars: {
          'playsinline': 1
        },
        events: {
          'onReady': onYouTubePlayerReady,
        }
      });
    });
  };

  // YouTube player API looks for this function when initialized.
  // We cannot rename this function and it must be on the window scope.
  window.onYouTubeIframeAPIReady = function() {
    window.YouTubeAPIReady = true;
    window.playLazyYouTube();
  };

  // Add YouTube player API script.
  const addYouTubeIFrameApi = function () {
    // Prevent adding the YouTube JS API to the page more than once.
    if (YouTubeJSIncluded) {
      return;
    }
    YouTubeJSIncluded = true;

    const tag = document.createElement('script');
    tag.src = "https://www.youtube.com/iframe_api";
    const firstScriptTag = document.getElementsByTagName('script')[0];
    firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
  };

  const playVimeo = function (iframe) {
    // Ensure we load the Vimeo JS only once.
    if (!VimeoJSIncluded) {
      VimeoJSIncluded = true;
      const tag = document.createElement('script');
      tag.src = 'https://player.vimeo.com/api/player.js';
      const firstScriptTag = document.getElementsByTagName('script')[0];
      // TODO: This should have the same treatment as YouTube videos.
      // We only load the player API once, but what if someone clicks 3 Vimeo
      // placeholders at once? We need to track the latest click and only auto
      // play that one.
      tag.onload = function () {
        VimeoAPIReady = true;
        const player = new Vimeo.Player(iframe);
        player.play();
      };
      firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
    } else {
      const player = new Vimeo.Player(iframe);
      player.play();
    }
  };

  // Create an iframe for a video embed.
  const genericFrame = function (src, aspect, width, height, fullscreen, title) {
    const frame = document.createElement('iframe');
    src = src.includes('?') ? src + '&' : src + '?';

    if (title) {
      frame.setAttribute('title', title);
    }
    frame.setAttribute('src', src);
    frame.setAttribute('width', width);
    frame.setAttribute('height', height);
    frame.style.aspectRatio = `${width} / ${height}`;
    frame.setAttribute('allow', 'autoplay; fullscreen=allowfullscreen');
    frame.setAttribute('allowFullScreen', '');

    if (fullscreen) {
      frame.setAttribute('allow', 'autoplay; fullscreen=allowfullscreen');
      frame.setAttribute('allowFullScreen', '');
    } else {
      frame.setAttribute('allow', 'autoplay');
    }

    // this is for vimeo only.
    frame.classList.add(`aspect-${aspect}`, 'lazy-player-frame');
    if (src.indexOf('vimeo') > 0) {
      frame.classList.add('lazy-vimeo-frame');
    }

    return frame;
  };

  // Create a YouTube frame using the YouTube Embed API.
  const createAndPlayYouTubeEmbed = function (placeholderButtonEl, location, src, aspect, width, height, fullscreen, title) {

    // Stop waiting for any other videos.
    LastYouTubeVideoSrcClicked = src;

    // Get scripts ready.
    addYouTubeIFrameApi();

    // Create frame.
    const frame = genericFrame(src, aspect, width, height, fullscreen, title);
    frame.id = `lazy-yt-${unique()}`;

    let frameSource = frame.getAttribute('src');
    if (frameSource.indexOf('enablejsapi') === -1) {
      frameSource += 'enablejsapi=1';
    }
    if (frameSource.indexOf('origin') === -1) {
      frameSource += `&origin=${window.location.origin}`;
    }
    frame.setAttribute('src', frameSource);

    frame.classList.add(`aspect-${aspect}`, 'lazy-youtube', 'lazy-player-frame');

    placeholderButtonEl.insertAdjacentElement(location, frame);

    if (window.YouTubeAPIReady) {
      // If API is not ready, it will automatically call this when it is.
      window.playLazyYouTube();
    }

    return frame;
  };

  // Replace the placeholder with the video embed.
  const replaceInPlace = function(placeholderButtonEl, location, src, aspect, width, height, fullscreen, title) {
    let frame;

    if (src.includes('youtube.com/')) {
      frame = createAndPlayYouTubeEmbed(placeholderButtonEl, location, src, aspect, width, height, fullscreen, title);
    }
    else {
      frame = genericFrame(src, aspect, width, height, fullscreen, title);
      placeholderButtonEl.insertAdjacentElement(location, frame);
      // We know we can programmatically start Vimeo videos, but not other
      // generic video sources.
      if (src.includes('vimeo')) {
        playVimeo(frame);
      }
    }

    return frame;
  };

  const launchModal = function (placeholderButtonEl, src, aspect, title) {
    const dialog = document.createElement('dialog');
    dialog.classList.add('lazy-video-dialog');
    const insertAt = document.createElement('button');
    insertAt.classList.add('lazy-dialog-close', 'btn');
    insertAt.setAttribute('aria-label', 'Close video');
    insertAt.textContent = '×';
    insertAt.addEventListener('click', ()=> {
      dialog.close();
      dialog.parentNode.removeChild(dialog);
    });
    dialog.appendChild(insertAt);
    placeholderButtonEl.insertAdjacentElement('beforebegin', dialog);
    if (src) {
      const height = aspect === '16x9' ? 1080 : 1440;
      replaceInPlace(insertAt, 'afterend', src, aspect, 1920, height, false, title);
    } else {
      const iframe = placeholderButtonEl.parentElement.querySelector('iframe').cloneNode(true);
      iframe.classList.add(`aspect-${aspect}`, 'lazy-player-frame');
      insertAt.insertAdjacentElement('afterend', iframe);
      if (iframe.dataset.lazySrc) {
        iframe.setAttribute('src', iframe.dataset.lazySrc);
      }
    }
    dialog.showModal();
  };

  // Pick playback method based on frame size.
  const handlePlaceholderButtonPress = function (placeholderButtonEl, title) {
    // The lazy video embed has a data attribute containing the rendered HTML
    // for the video embed. Extract the video src from that by double splitting
    // the HTML src attribute.
    let videoSrc = placeholderButtonEl.querySelector('.lazy-video-embed').dataset.lazyVideoEmbed;
    videoSrc = videoSrc.split('src="')[1];
    videoSrc = videoSrc.split('"')[0];

    const aspect = placeholderButtonEl.dataset.lazyAspect;

    const placeholderImage = placeholderButtonEl.querySelector('img');
    const width = placeholderImage.getAttribute('width');
    const height = placeholderImage.getAttribute('height');

    // Use a modal for displaying the video if we think it would be too small
    // where it is in the DOM now.
    if (placeholderButtonEl.offsetWidth < 500) {
      launchModal(placeholderButtonEl, videoSrc, aspect, title);
    } else {
      const frame = replaceInPlace(placeholderButtonEl, 'beforebegin', videoSrc, aspect, width, height, true, title);
      frame.focus();
    }
  };

  Drupal.behaviors.lazyVideo = {
    attach(context) {
      const elements = once('lazy-video', '.media--type-video', context);
      elements.forEach((element) => {
        const frame = element.querySelector('iframe');
        const title = element.dataset.videoTitle;
        if (frame && title) {
          if (!frame.title) {
            frame.setAttribute('title', title);
          }
        } else {
          const placeholderButtonEl = element.querySelector('.lazy-video');
          if (placeholderButtonEl) {
            placeholderButtonEl.addEventListener('click', () => handlePlaceholderButtonPress(placeholderButtonEl, title));
          }
        }
      });
    }
  };

}(Drupal, once));
