import React from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';

const VideoComponent = ({ source }: { source: string }) => {
  const router = useRouter();

  const handleRedirect = (path: string) => {
    router.push(path);
  };
  return (
    <div style={{ width: '100%', height: '75vh', position: 'relative', overflow: 'hidden' }}>
      <video
        src={source}
        autoPlay
        loop
        muted
        playsInline
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
        }}
      />
      {/* Tint overlay */}
      <div className="absolute inset-0 bg-black opacity-40 pointer-events-none"></div>

    {/* Overlay content */}
    <div className="video-overlay absolute inset-0 flex flex-col justify-center items-center text-center text-white px-4">
        <h1 className="text-4xl font-bold mb-8">AI Arena</h1>
        <h2 className="text-2xl mb-8">Compete with your AI models</h2>
        <div className="flex flex-wrap justify-around w-80">
          <button
            onClick={() => handleRedirect('/watch')}
            className="bg-blue-500 hover:bg-blue-700 text-white font-semibold py-2 px-6 rounded-full shadow-lg transition duration-300 ease-in-out transform hover:scale-105"
          >
            Watch
          </button>
          <button
            onClick={() => handleRedirect('/play')}
            className="bg-green-500 hover:bg-green-700 text-white font-semibold py-2 px-6 rounded-full shadow-lg transition duration-300 ease-in-out transform hover:scale-105"
          >
            Play
          </button>
        </div>
      
      </div>
    </div>
  );
};

export default VideoComponent;


// return (
//   <div style={{ width: '100%', height: '75vh', position: 'relative', overflow: 'hidden' }}>
//     <video
//       src={source}
//       autoPlay
//       loop
//       muted
//       playsInline
//       style={{
//         width: '100%',
//         height: '100%',
//         objectFit: 'cover',
//       }}
//     />
//     {/* Tint overlay */}
//     <div className="absolute inset-0 bg-black opacity-20 pointer-events-none"></div>

//     {/* Overlay content */}
//     <div className="video-overlay absolute inset-0 flex flex-col justify-center items-center text-center text-white px-4">
//       <h1 className="text-4xl font-bold mb-8">AI Arena</h1>
//       <h2 className="text-2xl mb-8">Compete with your AI models</h2>
//       <div className="flex flex-wrap justify-around w-full">
//         <button
//           onClick={() => handleRedirect('/watch')}
//           className="bg-blue-500 hover:bg-blue-700 text-white font-semibold py-2 px-6 rounded-full shadow-lg transition duration-300 ease-in-out transform hover:scale-105 mb-4 md:mb-0"
//         >
//           Watch
//         </button>
//         <button
//           onClick={() => handleRedirect('/play')}
//           className="bg-green-500 hover:bg-green-700 text-white font-semibold py-2 px-6 rounded-full shadow-lg transition duration-300 ease-in-out transform hover:scale-105"
//         >
//           Play
//         </button>
//       </div>
//     </div>
//   </div>
// );
// };

// export default VideoComponent;