#include <linux/device.h>
#include <linux/scatterlist.h>
#include <linux/mm_types.h>
#include <linux/dma-direction.h>
#include <linux/instr.h>
#include <linux/drifuzz.h>

inline void instr_dma_map_single(dma_addr_t addr, struct device *dev, 
                void *ptr, size_t size, int direction, 
                                unsigned long attrs) {
	// printk(KERN_INFO "Device [%s] dma map pointer [%px] size [%lu]"
    // 		" dir [%u] to dma_addr [%llx]\n", 
    //         	dev->driver->name, ptr, size, direction, addr);
    if ((direction == DMA_BIDIRECTIONAL ||
        direction == DMA_FROM_DEVICE))
	    handle_stream_dma_init((uint64_t)addr, (uint64_t)ptr, size);
}
EXPORT_SYMBOL(instr_dma_map_single);

inline void instr_dma_unmap_single(struct device *dev, dma_addr_t addr,
		size_t size, int direction, unsigned long attrs) {
	// printk(KERN_INFO "Device [%s] dma unmap dma_addr [%llx] size [%lu]"
	// 	" dir [%u]\n",
	// 	dev->driver->name, addr, size, direction);
    if ((direction == DMA_BIDIRECTIONAL ||
        direction == DMA_FROM_DEVICE))
	    handle_stream_dma_exit((uint64_t)addr);
}
EXPORT_SYMBOL(instr_dma_unmap_single);

inline void instr_dma_map_page(dma_addr_t addr, struct device *dev,
        struct page* page, size_t offset, size_t size, int direction,
        unsigned long attrs) {
    // printk(KERN_INFO "Device [%s] dma map page with offset [%lu]"
    //     " size[%lu] dir [%u] to dma_addr [%llx]\n",
    //     dev->driver->name, offset, size, direction, addr);
}
EXPORT_SYMBOL(instr_dma_map_page);

inline void instr_dma_unmap_page(struct device *dev, dma_addr_t addr,
        size_t size, int direction, unsigned long attrs) {
    // printk(KERN_INFO "Device [%s] dma unmap page dma_addr [%llx]"
    //     " size[%lu] dir [%u]\n",
    //     dev->driver->name, addr, size, direction);
}
EXPORT_SYMBOL(instr_dma_unmap_page);

inline void instr_dma_map_sg(int ents, struct device*dev,
        struct scatterlist *sgl, int nents, int direction, 
        unsigned long attrs) {
    int i;
    struct scatterlist *sg;

    // printk(KERN_INFO "Device dma map scatterlist begin\n");
    // for_each_sg(sgl, sg, nents, i) {
    //     printk(KERN_INFO "Device [%s] dma map page with offset [%u]"
    //         " size[%u] dir [%u] to dma_addr [%llx]\n",
    //         dev->driver->name, sg->offset, sg->length, direction, 
    //         sg->dma_address);
    // }
    // printk(KERN_INFO "Device dma map scatterlist end\n");

}
EXPORT_SYMBOL(instr_dma_map_sg);

inline void instr_dma_unmap_sg(struct device *dev, struct scatterlist *sgl,
        int nents, int direction, unsigned long attrs) {
    int i;
    struct scatterlist *sg;

    // printk(KERN_INFO "Device dma unmap scatterlist begin\n");
    // for_each_sg(sgl, sg, nents, i) {
    //     printk(KERN_INFO "Device [%s] dma unmap dma_addr [%llx]"
    //         " size[%u] dir [%u]",
    //         dev->driver->name, sg->dma_address, sg->length, direction);
    // }
    // printk(KERN_INFO "Device dma unmap scatterlist end\n");
}
EXPORT_SYMBOL(instr_dma_unmap_sg);

inline void instr_request_irq(int res, unsigned int irq, 
        void *handler, unsigned long flags, const char *name, 
        void *dev) {
	printk(KERN_INFO "Device [%s] request irq [%u] res [%d] handler [%p]\n",
			name, irq, res, (void*)handler);
}
EXPORT_SYMBOL(instr_request_irq);
