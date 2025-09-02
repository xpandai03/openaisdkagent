import React, { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  ZoomIn, 
  ZoomOut, 
  Maximize2, 
  Download,
  ChevronLeft,
  ChevronRight
} from 'lucide-react'

interface Screenshot {
  id: string
  image: string // base64 or URL
  timestamp: number
  action?: string
  description?: string
}

interface ScreenshotViewerProps {
  screenshots: Screenshot[]
  className?: string
}

export function ScreenshotViewer({ screenshots, className = '' }: ScreenshotViewerProps) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [zoom, setZoom] = useState(1)
  
  if (!screenshots || screenshots.length === 0) {
    return null
  }
  
  const current = screenshots[currentIndex]
  
  const handlePrevious = () => {
    setCurrentIndex((prev) => (prev > 0 ? prev - 1 : screenshots.length - 1))
  }
  
  const handleNext = () => {
    setCurrentIndex((prev) => (prev < screenshots.length - 1 ? prev + 1 : 0))
  }
  
  const handleZoomIn = () => {
    setZoom((prev) => Math.min(prev + 0.25, 3))
  }
  
  const handleZoomOut = () => {
    setZoom((prev) => Math.max(prev - 0.25, 0.5))
  }
  
  const handleDownload = () => {
    const link = document.createElement('a')
    link.download = `screenshot-${current.id}.png`
    link.href = current.image.startsWith('data:') 
      ? current.image 
      : `data:image/png;base64,${current.image}`
    link.click()
  }
  
  const imageUrl = current.image.startsWith('data:') 
    ? current.image 
    : `data:image/png;base64,${current.image}`
  
  return (
    <>
      <div className={`border rounded-lg p-4 ${className}`}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Badge variant="outline">
              {currentIndex + 1} / {screenshots.length}
            </Badge>
            {current.action && (
              <Badge variant="secondary">{current.action}</Badge>
            )}
          </div>
          
          <div className="flex items-center gap-1">
            <Button
              size="icon"
              variant="ghost"
              onClick={handlePrevious}
              disabled={screenshots.length <= 1}
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            
            <Button
              size="icon"
              variant="ghost"
              onClick={handleNext}
              disabled={screenshots.length <= 1}
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
            
            <Button
              size="icon"
              variant="ghost"
              onClick={handleZoomOut}
              disabled={zoom <= 0.5}
            >
              <ZoomOut className="w-4 h-4" />
            </Button>
            
            <Button
              size="icon"
              variant="ghost"
              onClick={handleZoomIn}
              disabled={zoom >= 3}
            >
              <ZoomIn className="w-4 h-4" />
            </Button>
            
            <Button
              size="icon"
              variant="ghost"
              onClick={() => setIsFullscreen(true)}
            >
              <Maximize2 className="w-4 h-4" />
            </Button>
            
            <Button
              size="icon"
              variant="ghost"
              onClick={handleDownload}
            >
              <Download className="w-4 h-4" />
            </Button>
          </div>
        </div>
        
        <div className="relative overflow-hidden rounded border bg-muted/20">
          <div 
            className="overflow-auto max-h-[400px]"
            style={{ cursor: zoom > 1 ? 'move' : 'default' }}
          >
            <img
              src={imageUrl}
              alt={current.description || `Screenshot ${current.id}`}
              className="transition-transform duration-200"
              style={{ 
                transform: `scale(${zoom})`,
                transformOrigin: 'center center',
                maxWidth: zoom > 1 ? 'none' : '100%'
              }}
            />
          </div>
        </div>
        
        {current.description && (
          <p className="text-sm text-muted-foreground mt-2">
            {current.description}
          </p>
        )}
      </div>
      
      <Dialog open={isFullscreen} onOpenChange={setIsFullscreen}>
        <DialogContent className="max-w-[90vw] max-h-[90vh]">
          <DialogHeader>
            <DialogTitle>
              Screenshot {currentIndex + 1} of {screenshots.length}
              {current.action && ` - ${current.action}`}
            </DialogTitle>
          </DialogHeader>
          
          <div className="relative overflow-auto">
            <img
              src={imageUrl}
              alt={current.description || `Screenshot ${current.id}`}
              className="w-full h-auto"
            />
          </div>
          
          <div className="flex justify-between mt-4">
            <Button
              variant="outline"
              onClick={handlePrevious}
              disabled={screenshots.length <= 1}
            >
              <ChevronLeft className="w-4 h-4 mr-2" />
              Previous
            </Button>
            
            <Button
              variant="outline"
              onClick={handleNext}
              disabled={screenshots.length <= 1}
            >
              Next
              <ChevronRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}