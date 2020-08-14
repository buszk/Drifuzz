/* instrument dma-mapping.h */
#ifndef _INSTR_DMA_H
#ifdef _LINUX_DMA_MAPPING_H
#define _INSTR_DMA_H
inline void instr_dma_map_single(dma_addr_t addr, struct device *dev, 
        void *ptr, size_t size, int direction, unsigned long attrs);
inline void instr_dma_unmap_single(struct device *dev, dma_addr_t addr,
	size_t size, int direction, unsigned long attrs);
inline void instr_dma_map_page(dma_addr_t addr, struct device *dev,
        struct page* page, size_t offset, size_t size, int direction,
        unsigned long attrs);
inline void instr_dma_unmap_page(struct device *dev, dma_addr_t addr,
        size_t size, int direction, unsigned long attrs);
inline void instr_dma_map_sg(int ents, struct device*dev,
        struct scatterlist *sg, int nents, int direction, 
        unsigned long attrs);
inline void instr_dma_unmap_sg(struct device *dev, struct scatterlist *g,
        int nents, int dir, unsigned long attrs);
#endif
#endif
/* instrument interrupt.h */
#ifndef _INSTR_INTERRUPT_H
#ifdef _LINUX_INTERRUPT_H
#define _INSTR_INTERRUPT_H
inline void instr_request_irq(int res, unsigned int irq, 
        void *handler, unsigned long flags, const char *name, 
        void *dev);
#endif
#endif