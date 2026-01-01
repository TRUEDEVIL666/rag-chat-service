export const getDefaultParams = (method) => {
  switch (method) {
    case 'sentence':
      return { chunkSize: 1000, chunkOverlap: 200 };
    case 'token':
      return { chunkSize: 512, chunkOverlap: 50 };
    case 'character':
      return { chunkSize: 1000, chunkOverlap: 200, separator: '\\n\\n' };
    case 'word':
      return { chunkSize: 1000, chunkOverlap: 200 };
    case 'sliding':
      return { windowSize: 3 };
    case 'semantic':
      return { bufferSize: 1, thresholdPercentage: 95 };
    case 'hierarchical':
      return { chunkSizes: '2048, 512, 128' };
    case 'recursive':
      return { chunkSize: 1000, chunkOverlap: 200 };
    default:
      return {};
  }
};

export const calculateChunks = (text, method, params) => {
  if (!text) return [];
  
  let chunksDisplay = [];
  const { 
    chunkSize, chunkOverlap, windowSize, 
    separator 
  } = params;

  // Helper to parse int safe
  const pInt = (val, def) => parseInt(val) || def;

  switch (method) {
    case 'sentence': {
      // 1. Split text into sentences using regex
      // Matches sentence ending punctuation (.!?) followed by space or end of string
      const sentences = text.match(/[^.!?]+[.!?]+["']?|[^.!?]+$/g);
      
      if (!sentences) {
        chunksDisplay = [text];
        break;
      }

      const cSizeSent = pInt(chunkSize, 1024);
      const cOverlapSent = pInt(chunkOverlap, 200);

      let currentChunk = [];
      let currentLength = 0;

      for (let i = 0; i < sentences.length; i++) {
        const sentence = sentences[i];
        const sentenceLen = sentence.length;

        // If adding this sentence exceeds the limit...
        if (currentLength + sentenceLen > cSizeSent) {
          // 1. Push the current valid chunk if it exists
          if (currentChunk.length > 0) {
            chunksDisplay.push(currentChunk.join("").trim());
            
            // Prepare overlap for the NEXT chunk from the items we just pushed
            let overlapChunk = [];
            let overlapLength = 0;
            for (let j = currentChunk.length - 1; j >= 0; j--) {
               const s = currentChunk[j];
               if (overlapLength + s.length <= cOverlapSent) {
                 overlapChunk.unshift(s);
                 overlapLength += s.length;
               } else {
                 break;
               }
            }
            currentChunk = [...overlapChunk];
            currentLength = overlapLength;
          }

          // 2. Now check if the NEW sentence ITSELF is too big to fit in an empty chunk?
          // (i.e., we just flushed, so currentLength is small (just overlap), or 0)
          // Actually, if we have overlap, we try to append. If it fails, does it fail because of overlap + sentence > limit?
          // If so, we might need to drop overlap and see if sentence alone fits. 
          // But usually we want to force split the sentence if it is > cSizeSent alone.
          
          if (currentLength + sentenceLen > cSizeSent) {
              // Even with a fresh/overlap start, it's too big.
              // Check if sentence alone is too big
              if (sentenceLen > cSizeSent) {
                  // Case: Sentence is massive. We must split it strictly by characters.
                  // First, push whatever overlap we had (as a separate chunk? or discard?)
                  // Usually, we just push the overlap chunk as is if we haven't already? 
                  // Actually we haven't pushed the 'next' version of overlap yet.
                  // Let's simplified: If we have pending overlap content, push it to be safe? 
                  // Or just clear it.
                  
                  // For simplicity in this preview: Clear current buffer and force split the huge sentence
                  if (currentChunk.length > 0) {
                      chunksDisplay.push(currentChunk.join("").trim());
                      currentChunk = [];
                      currentLength = 0;
                  }
                  
                  // Force split the long sentence
                  let ptr = 0;
                  while (ptr < sentenceLen) {
                      let end = Math.min(ptr + cSizeSent, sentenceLen);
                      const slice = sentence.substring(ptr, end);
                      chunksDisplay.push(slice);
                      
                      // For the next slice, we move forward effectively by size - overlap
                      // But we must ensure progress.
                      const step = Math.max(1, cSizeSent - cOverlapSent);
                      if (end === sentenceLen) break; 
                      ptr += step;
                  }
                  continue; // Done with this sentence
              }
              
              // Case: Sentence fits alone, but not with overlap.
              // So just start a new chunk with ONLY this sentence (drop overlap)
              currentChunk = [sentence];
              currentLength = sentenceLen;
              continue;
          }
        }
        
        // If it fits (either originally, or after flush), add it
        currentChunk.push(sentence);
        currentLength += sentenceLen;
      }

      // Push the last remaining chunk
      if (currentChunk.length > 0) {
        chunksDisplay.push(currentChunk.join("").trim());
      }
      break;
    }

    case 'semantic':
      chunksDisplay = text.split(/\n\s*\n/).filter(c => c.trim());
      break;

    case 'token': {
      const wordsToken = text.split(/\s+/);
      const cSizeToken = pInt(chunkSize, 512);
      const cOverlapToken = pInt(chunkOverlap, 50);
      const stepToken = cSizeToken - cOverlapToken > 0 ? cSizeToken - cOverlapToken : cSizeToken;

      for (let i = 0; i < wordsToken.length; i += stepToken) {
        const chunk = wordsToken.slice(i, i + cSizeToken).join(" ");
        if (chunk) chunksDisplay.push(chunk + "...");
        if (i + cSizeToken >= wordsToken.length) break;
      }
      break;
    }

    case 'character': {
      const cSizeChar = pInt(chunkSize, 1024);
      const cOverlapChar = pInt(chunkOverlap, 200);
      const stepChar = cSizeChar - cOverlapChar > 0 ? cSizeChar - cOverlapChar : cSizeChar;

      for (let i = 0; i < text.length; i += stepChar) {
        chunksDisplay.push(text.substring(i, i + cSizeChar));
        if (i + cSizeChar >= text.length) break;
      }
      break;
    }

    case 'word': {
      const words = text.split(/\s+/);
      const cSizeWord = pInt(chunkSize, 1000);
      const cOverlapWord = pInt(chunkOverlap, 200);
      const stepWord = cSizeWord - cOverlapWord > 0 ? cSizeWord - cOverlapWord : cSizeWord;

      for (let i = 0; i < words.length; i += stepWord) {
        chunksDisplay.push(words.slice(i, i + cSizeWord).join(" "));
        if (i + cSizeWord >= words.length) break;
      }
      break;
    }

    case 'recursive': {
        const cSizeRec = pInt(chunkSize, 1000);
        // Ensure overlap is strictly less than chunk size to prevent accumulation
        let cOverlapRec = pInt(chunkOverlap, 200);
        if (cOverlapRec >= cSizeRec) {
          cOverlapRec = Math.max(0, cSizeRec - 1);
        }
        
        const recursiveSplit = (text, separators) => {
          const finalChunks = [];
          
          if (text.length <= cSizeRec) {
            return [text];
          }
          
          if (separators.length === 0) {
            // No more separators, hard split by character
             for (let i = 0; i < text.length; i += cSizeRec - cOverlapRec) {
                finalChunks.push(text.substring(i, i + cSizeRec));
             }
             return finalChunks;
          }
          
          const sep = separators[0];
          const nextSeparators = separators.slice(1);
          
          // Escape generic regex characters if sep is a string literal (like ' ')
          // But for now, we assume standard string separators.
          // Note: split by regex \n\n might be needed if user input is literal \n\n
          let splits = [];
          if (sep === '\\n\\n') splits = text.split(/\n\s*\n/);
          else if (sep === '\\n') splits = text.split('\n');
          else splits = text.split(sep);
          
          let currentChunk = [];
          let currentLen = 0;
          
          for (const s of splits) {
             const sLen = s.length;
             const sepLen = currentChunk.length > 0 ? sep.length : 0;
             
             if (currentLen + sLen + sepLen > cSizeRec) {
                // Buffer is full, flush it
                if (currentChunk.length > 0) {
                    finalChunks.push(currentChunk.join(sep));
                    
                    // Create overlap for next chunk
                     const overlapLimit = cOverlapRec;
                     let overlapBuf = [];
                     let overlapLen = 0;
                     for (let k = currentChunk.length - 1; k >= 0; k--) {
                        const part = currentChunk[k];
                        const partSepLen = overlapBuf.length > 0 ? sep.length : 0;
                        if (overlapLen + part.length + partSepLen <= overlapLimit) {
                            overlapBuf.unshift(part);
                            overlapLen += part.length + partSepLen;
                        } else {
                            break;
                        }
                     }
                     currentChunk = overlapBuf;
                     currentLen = overlapLen;
                }
                
                // Re-check: Does 's' fit with the overlap?
                const newSepLen = currentChunk.length > 0 ? sep.length : 0;
                
                if (currentLen + sLen + newSepLen > cSizeRec) {
                    // It doesn't fit with overlap. 
                    // Strategy: Drop overlap to try and fit 's'.
                    currentChunk = [];
                    currentLen = 0;
                    
                    if (sLen > cSizeRec) {
                        // 's' is too big even alone -> Recurse/Split it further
                        finalChunks.push(...recursiveSplit(s, nextSeparators));
                    } else {
                        // 's' fits alone
                        currentChunk.push(s);
                        currentLen = sLen;
                    }
                } else {
                    // Fits with overlap
                    currentChunk.push(s);
                    currentLen += sLen + newSepLen;
                }
             } else {
                // Fits in current buffer
                currentChunk.push(s);
                currentLen += sLen + sepLen;
             }
          }
          
          if (currentChunk.length > 0) {
             finalChunks.push(currentChunk.join(sep));
          }
          
          return finalChunks;
        };
        
        // Define hierarchy of separators
        const defaultSeparators = ['\\n\\n', '\\n', ' ', ''];
        chunksDisplay = recursiveSplit(text, defaultSeparators);
        break;
    }

    case 'hierarchical': {
      const p_hier = text.split(/\n\s*\n/);
      chunksDisplay = p_hier.map((p, idx) => ({
        type: 'hierarchical',
        parentIdx: idx,
        text: p.split('.')[0] + "...",
        childrenCount: p.split('. ').length
      }));
      break;
    }

    case 'sliding': {
      const wSize = pInt(windowSize, 3);
      const s_slide = text.match(/[^.!?]+[.!?]+["']?|[^.!?]+$/g)?.map(s => s.trim()) || [text];
      for (let i = 0; i < s_slide.length - wSize + 1; i++) {
        let windowHalo = [];
        for (let j = 0; j < wSize; j++) {
          if (i + j < s_slide.length) windowHalo.push(s_slide[i + j]);
        }
        chunksDisplay.push(`[Window ${i}]: ` + windowHalo.join(" "));
      }
      if (s_slide.length < wSize && s_slide.length > 0) chunksDisplay.push(s_slide.join(" "));
      break;
    }

    default:
      chunksDisplay = [text];
  }
  
  return chunksDisplay;
};
