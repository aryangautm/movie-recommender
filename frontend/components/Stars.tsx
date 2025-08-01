import React, { useState, useEffect, useRef, useMemo } from 'react';

// --- CONFIGURATION ---
const INTERACTION_RADIUS = 80; // How close the mouse needs to be to affect a star (in pixels)
const MAX_DISPLACEMENT = 40;   // How far a star can be pushed away (in pixels)

// --- TYPES ---
interface StarData {
  id: number;
  top: string;
  left: string;
  size: number;
  animationDelay: string;
}

interface MousePos {
  x: number;
  y: number;
}

interface StarsProps {
  numStars?: number;
  mousePos: MousePos;
}

// --- SINGLE STAR COMPONENT ---
// This component handles the logic for one star's interaction
const StarItem: React.FC<{ data: StarData; mousePos: MousePos }> = ({ data, mousePos }) => {
  const starRef = useRef<HTMLDivElement>(null);
  const [transform, setTransform] = useState('translate(0px, 0px)');

  useEffect(() => {
    if (!starRef.current || mousePos.x === 0) return;

    // Get the star's center position
    const starRect = starRef.current.getBoundingClientRect();
    const starX = starRect.left + starRect.width / 2;
    const starY = starRect.top + starRect.height / 2;

    // Calculate distance and vector from mouse to star
    const dx = starX - mousePos.x;
    const dy = starY - mousePos.y;
    const distance = Math.sqrt(dx * dx + dy * dy);

    // If the mouse is close enough, calculate the displacement
    if (distance < INTERACTION_RADIUS) {
      const force = 1 - (distance / INTERACTION_RADIUS);
      const moveX = (dx / distance) * force * MAX_DISPLACEMENT;
      const moveY = (dy / distance) * force * MAX_DISPLACEMENT;
      setTransform(`translate(${moveX}px, ${moveY}px)`);
    } else {
      // If the mouse is far away, reset to original position
      setTransform('translate(0px, 0px)');
    }
  }, [mousePos]); // Re-run this logic every time the mouse moves

  return (
    <div
      ref={starRef}
      className="star"
      style={{
        top: data.top,
        left: data.left,
        width: `${data.size}px`,
        height: `${data.size}px`,
        animationDelay: data.animationDelay,
        transform: transform, // Apply the dynamic transform
      }}
    />
  );
};


// --- MAIN STARS CONTAINER ---
const Stars: React.FC<StarsProps> = ({ numStars = 150, mousePos }) => {
  // We use useMemo to prevent re-generating stars on every mouse move
  const stars = useMemo(() => {
    const newStars: StarData[] = [];
    for (let i = 0; i < numStars; i++) {
      newStars.push({
        id: i,
        top: `${Math.random() * 40}%`,
        left: `${Math.random() * 100}%`,
        size: Math.random() * 2 + 1,
        animationDelay: `${Math.random() * 10}s`,
      });
    }
    return newStars;
  }, [numStars]);

  return (
    <div className="absolute top-0 left-0 w-full h-full overflow-hidden z-0">
      {stars.map((starData) => (
        <StarItem key={starData.id} data={starData} mousePos={mousePos} />
      ))}
    </div>
  );
};

export default Stars;