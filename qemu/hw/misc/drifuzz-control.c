#include "qemu/osdep.h"
#include "hw/pci/pci.h"
#include "hw/pci/msi.h"
#include "hw/pci/msix.h"
#include "hw/hw.h"
#include "hw/qdev-properties.h"
#include "migration/vmstate.h"
#include "net/net.h"
#include "sysemu/sysemu.h"
#include "sysemu/dma.h"
#include "qemu/module.h"
#include "qemu/range.h"
#include "qapi/error.h"

typedef struct DrifuzzState_st {
	PCIDevice parent_obj;
	
	MemoryRegion mmio;
	char memory [0x1000];
} DrifuzzState;

typedef struct DrifuzzClass {
	PCIDeviceClass parent_class;
} DrifuzzClass;

#define DRIFUZZ(obj) \
	OBJECT_CHECK(DrifuzzState, (obj), TYPE_PCI_DEVICE)

static void drifuzz_class_init(ObjectClass *klass, void *data);
static void pci_drifuzz_realize(PCIDevice *pci_dev, Error **errp);
static void drifuzz_instance_init(Object *obj);
static void drifuzz_register_types(void);
static const MemoryRegionOps drifuzz_mmio_ops;
/*
static Property drifuzz_properties[] = {
	DEFINE_PROP_END_OF_LIST(),
};
*/
/* Shared */
enum ACTIONS {
	DMA_INIT = 1,
	DMA_EXIT
};

static uint64_t read_mem (char* mem, hwaddr addr, unsigned size) {
	uint8_t *offset_addr = (uint8_t*) mem + addr;
	switch (size)
	{
	case 1:
		// uint8_t *p = (uint8_t*)(mem + addr);
		return *(uint8_t*)offset_addr;
	case 2:
		// uint16_t *p = (uint16_t*)(mem + addr);
		return *(uint16_t*)offset_addr;
	case 4:
		// uint32_t *p = (uint32_t*)(mem + addr);
		return *(uint32_t*)offset_addr;
	case 8:
		// uint64_t *p = (uint64_t*)(mem + addr);
		return *(uint64_t*)offset_addr;
	default:
		assert("wrong size" && false);
		return 0;
	}
}

static void write_mem (char* mem, hwaddr addr, uint64_t val, unsigned size) {
	uint8_t *offset_addr = (uint8_t*) mem + addr;
	switch (size)
	{
	case 1:
		// uint8_t *p = (uint8_t*)(mem + addr);
		*(uint8_t*)offset_addr = val & 0xff;
		break;
	case 2:
		// uint16_t *p = (uint16_t*)(mem + addr);
		*(uint16_t*)offset_addr = val & 0xffff;
		break;
	case 4:
		// uint32_t *p = (uint32_t*)(mem + addr);
		*(uint32_t*)offset_addr = val & 0xffffffff;
		break;
	case 8:
		// uint64_t *p = (uint64_t*)(mem + addr);
		*(uint64_t*)offset_addr = val;
		break;
	default:
		assert("wrong size" && false);
		break;
	}
}

static void handle_dma_init(void *opaque, uint64_t dma, uint64_t phy, 
		uint64_t size) {
	
	DrifuzzState *s = opaque;
	MemoryRegion *subregion;
	subregion = malloc(sizeof(*subregion));
	memory_region_init_io(subregion, OBJECT(s), &drifuzz_mmio_ops,
			// opaque, "drifuzz-dma-region", size);
			opaque, "drifuzz-dma-region", 0x1000);
	memory_region_add_subregion_overlap(get_system_memory(),
			phy, subregion, 100);
}


static void drifuzz_handle(void *opaque) {
	DrifuzzState *s = opaque;
	switch (read_mem(s->memory, 0x8, 0x8))
	{
	case DMA_INIT:
		handle_dma_init(opaque, 
				read_mem(s->memory, 0x10, 0x8),
				read_mem(s->memory, 0x18, 0x8),
				read_mem(s->memory, 0x20, 0x8));
		break;
	case DMA_EXIT:
		break;
	default:
		break;
	}
}

static uint64_t __drifuzz_mmio_read(void *opaque, hwaddr addr,
                              unsigned size) {
	DrifuzzState *s = opaque;
	return read_mem(s->memory, addr, size);
}
static uint64_t drifuzz_mmio_read(void *opaque, hwaddr addr,
                              unsigned size) {

    DrifuzzState *s = opaque;
	printf("drifuzz_mmio_read: %lx %u\n", addr, size);

    (void)s;
    return __drifuzz_mmio_read(opaque, addr, size);
}



static void drifuzz_mmio_write(void *opaque, hwaddr addr,
                           uint64_t val, unsigned size) {
    DrifuzzState *s = opaque;
	printf("drifuzz_mmio_write: %lx %lx %u\n", addr, val, size);
	write_mem(s->memory, addr, val, size);
	if (addr == 0) {
		drifuzz_handle(opaque);
	}
    (void)s;
}
static const MemoryRegionOps drifuzz_mmio_ops = {
    .read = drifuzz_mmio_read,
    .write = drifuzz_mmio_write,
    .endianness = DEVICE_LITTLE_ENDIAN,
	/*
    .impl = {
        .min_access_size = 4,
        .max_access_size = 4,
    },
	*/
};
/*
static uint64_t drifuzz_msix_table_mmio_read(void *opaque, hwaddr addr,
                              unsigned size) {

    //DrifuzzState *s = opaque;
	printf("msix_table_mmio_read: %lx %u\n", addr, size);

    return msix_table_mmio_read(opaque, addr, size);
}

static void drifuzz_msix_table_mmio_write(void *opaque, hwaddr addr,
                           uint64_t val, unsigned size) {
    //DrifuzzState *s = opaque;
	printf("msix_table_mmio_write: %lx %lx %u\n", addr, val, size);

    msix_table_mmio_write(opaque, addr, val, size);

}

static const MemoryRegionOps drifuzz_msix_table_mmio_ops = {
    .read = drifuzz_msix_table_mmio_read,
    .write = drifuzz_msix_table_mmio_write,
    .endianness = DEVICE_LITTLE_ENDIAN,
};

static uint64_t drifuzz_msix_pba_mmio_read(void *opaque, hwaddr addr,
                              unsigned size) {

    //DrifuzzState *s = opaque;
	printf("msix_pba_mmio_read: %lx %u\n", addr, size);

    return msix_pba_mmio_read(opaque, addr, size);
}

static void drifuzz_msix_pba_mmio_write(void *opaque, hwaddr addr,
                           uint64_t val, unsigned size) {
    //DrifuzzState *s = opaque;
	printf("msix_pba_mmio_write: %lx %lx %u\n", addr, val, size);

    msix_pba_mmio_write(opaque, addr, val, size);

}

static const MemoryRegionOps drifuzz_msix_pba_mmio_ops = {
    .read = drifuzz_msix_pba_mmio_read,
    .write = drifuzz_msix_pba_mmio_write,
    .endianness = DEVICE_LITTLE_ENDIAN,
};
*/
static void drifuzz_class_init(ObjectClass *klass, void *data) {
	printf("Entering drifuzz_class_init\n");
	DeviceClass *dc = DEVICE_CLASS(klass);
	PCIDeviceClass *k = PCI_DEVICE_CLASS(klass);

	k->realize = pci_drifuzz_realize;
	k->vendor_id = 0x7777;
	k->device_id = 0x7777;
	k->subsystem_vendor_id = 0x7777;
	k->subsystem_id = 0x7777;
	k->revision = 0;
	k->class_id = PCI_CLASS_COMMUNICATION_SERIAL;
	set_bit(DEVICE_CATEGORY_INPUT, dc->categories);

	//device_class_set_props(dc, drifuzz_properties);
	printf("Leaving drifuzz_class_init\n");
}
/*
static int drifuzz_add_pm_capability(PCIDevice *pdev) {
	Error *local_err = NULL;
	// offset 0 to auto mode
	uint8_t offset = 0;
	 
	int ret = pci_add_capability(pdev, PCI_CAP_ID_PM, offset,
			PCI_PM_SIZEOF, &local_err);
	if (local_err) {
		error_report_err(local_err);
	}
	return ret;
}

static int drifuzz_init_msix(PCIDevice *pdev) {
	DrifuzzState *d = DRIFUZZ(pdev);
	// More on magic numbers
    int res = __msix_init(PCI_DEVICE(d), 5,
                        &d->msix,
                        1, 0x0000, 
                        &d->msix,
                        1, 0x2000,
                        0xA0, NULL,
						&drifuzz_msix_table_mmio_ops,
						&drifuzz_msix_pba_mmio_ops);
	return res;
}
*/
static void pci_drifuzz_realize(PCIDevice *pci_dev, Error **errp) {
	printf("Entering pci_drifuzz_realize\n");
	//DeviceState *dev = DEVICE(pci_dev);
	DrifuzzState *d = DRIFUZZ(pci_dev);

    memory_region_init_io(&d->mmio, OBJECT(d), &drifuzz_mmio_ops, d,
                          "drifuzz-mmio", 0x10000);
    pci_register_bar(pci_dev, 0, PCI_BASE_ADDRESS_SPACE_MEMORY, &d->mmio);

	printf("Leaving pci_drifuzz_realize\n");
}

static void drifuzz_instance_init(Object *obj) {
	printf("Entering drifuzz_instance_init\n");
	//DrifuzzState *n = DRIFUZZ(obj);
    //(void*) n;
	printf("Leavin drifuzz_instance_init\n");
}

static const TypeInfo drifuzz_info = {
	.name          = "drifuzz",
	.parent        = TYPE_PCI_DEVICE,
	.instance_size = sizeof(DrifuzzState),
	.instance_init = drifuzz_instance_init,
	.class_size    = sizeof(DrifuzzClass),
	.abstract      = false,
	.class_init    = drifuzz_class_init,
	.instance_init = drifuzz_instance_init,
	.interfaces = (InterfaceInfo[]) {
		{ INTERFACE_CONVENTIONAL_PCI_DEVICE },
		{ },
	},
};

static void drifuzz_register_types(void) {
	printf("Entering drifuzz_register_types\n");
	type_register_static(&drifuzz_info);
	printf("Leaving drifuzz_register_types\n");
}

type_init(drifuzz_register_types)
