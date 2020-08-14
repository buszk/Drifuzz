/* consistent dma api */
void handle_const_dma_init(uint64_t dma_addr, uint64_t addr, uint64_t size);
void handle_const_dma_exit(uint64_t dma_addr);

/* streaming dma api */
void handle_stream_dma_init(uint64_t dma_addr, uint64_t addr, uint64_t size);
void handle_stream_dma_exit(uint64_t dma_addr);

/* kasan */
void handle_kasan(void);