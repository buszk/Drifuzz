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

typedef struct ATH10KState_st {
	PCIDevice parent_obj;
	
	NICState *nic;
	NICConf conf;
	MemoryRegion mmio;
	MemoryRegion io;
    MemoryRegion msix;
} ATH10KState;

typedef struct ATH10KClass {
	PCIDeviceClass parent_class;
} ATH10KClass;

#define ATH10K(obj) \
	OBJECT_CHECK(ATH10KState, (obj), TYPE_PCI_DEVICE)

static void ath10k_class_init(ObjectClass *klass, void *data);
static void pci_ath10k_realize(PCIDevice *pci_dev, Error **errp);
static void ath10k_instance_init(Object *obj);
static void ath10k_register_types(void);

static Property ath10k_properties[] = {
	DEFINE_NIC_PROPERTIES(ATH10KState, conf),
	DEFINE_PROP_END_OF_LIST(),
};

static uint64_t ath10k_mmio_read(void *opaque, hwaddr addr,
                              unsigned size) {

    ATH10KState *s = opaque;
    uint64_t res = 0;
	printf("mmio_read: %lx %u\n", addr, size);
    switch (addr)
    {
    case 0x80000:
        res = 3;
        break;
    case 0x3a028:
        res = 2;
        break;
    case 0x8f0:
        res = 0x400;
        break;
    default:
        break;
    }
    (void)s;
    return res;
}

static void ath10k_mmio_write(void *opaque, hwaddr addr,
                           uint64_t val, unsigned size) {
    ATH10KState *s = opaque;
	printf("mmio_write: %lx %lx %u\n", addr, val, size);

    (void)s;
}
static const MemoryRegionOps ath10k_mmio_ops = {
    .read = ath10k_mmio_read,
    .write = ath10k_mmio_write,
    .endianness = DEVICE_LITTLE_ENDIAN,
	/*
    .impl = {
        .min_access_size = 4,
        .max_access_size = 4,
    },
	*/
};

static uint64_t ath10k_msix_table_mmio_read(void *opaque, hwaddr addr,
                              unsigned size) {

    //ath10kState *s = opaque;
	printf("msix_table_mmio_read: %lx %u\n", addr, size);

    return msix_table_mmio_read(opaque, addr, size);
}

static void ath10k_msix_table_mmio_write(void *opaque, hwaddr addr,
                           uint64_t val, unsigned size) {
    //ath10kState *s = opaque;
	printf("msix_table_mmio_write: %lx %lx %u\n", addr, val, size);

    msix_table_mmio_write(opaque, addr, val, size);

}

static const MemoryRegionOps ath10k_msix_table_mmio_ops = {
    .read = ath10k_msix_table_mmio_read,
    .write = ath10k_msix_table_mmio_write,
    .endianness = DEVICE_LITTLE_ENDIAN,
};

static uint64_t ath10k_msix_pba_mmio_read(void *opaque, hwaddr addr,
                              unsigned size) {

    //ath10kState *s = opaque;
	printf("msix_pba_mmio_read: %lx %u\n", addr, size);

    return msix_pba_mmio_read(opaque, addr, size);
}

static void ath10k_msix_pba_mmio_write(void *opaque, hwaddr addr,
                           uint64_t val, unsigned size) {
    //ath10kState *s = opaque;
	printf("msix_pba_mmio_write: %lx %lx %u\n", addr, val, size);

    msix_pba_mmio_write(opaque, addr, val, size);

}

static const MemoryRegionOps ath10k_msix_pba_mmio_ops = {
    .read = ath10k_msix_pba_mmio_read,
    .write = ath10k_msix_pba_mmio_write,
    .endianness = DEVICE_LITTLE_ENDIAN,
};

static void ath10k_class_init(ObjectClass *klass, void *data) {
	printf("Entering ath10k_class_init\n");
	DeviceClass *dc = DEVICE_CLASS(klass);
	PCIDeviceClass *k = PCI_DEVICE_CLASS(klass);

	k->realize = pci_ath10k_realize;
	k->vendor_id = 0x168c;
	k->device_id = 0x003e;
	k->subsystem_vendor_id = 0x168c;
	k->subsystem_id = 0x003e;
	k->revision = 0;
	k->class_id = PCI_CLASS_NETWORK_OTHER;
	set_bit(DEVICE_CATEGORY_NETWORK, dc->categories);

	dc->props = ath10k_properties;
	printf("Leaving ath10k_class_init\n");
}

static int ath10k_add_pm_capability(PCIDevice *pdev) {
	Error *local_err = NULL;
	/* offset 0 to auto mode */
	uint8_t offset = 0;
	 
	int ret = pci_add_capability(pdev, PCI_CAP_ID_PM, offset,
			PCI_PM_SIZEOF, &local_err);
	if (local_err) {
		error_report_err(local_err);
	}
	return ret;
}

static int __attribute__((unused)) ath10k_init_msix(PCIDevice *pdev) {
	ATH10KState *d = ATH10K(pdev);
	/* More on magic numbers */
    int res = __msix_init(PCI_DEVICE(d), 5,
                        &d->msix,
                        1, 0x0000, 
                        &d->msix,
                        1, 0x2000,
                        0xA0, NULL,
						&ath10k_msix_table_mmio_ops,
						&ath10k_msix_pba_mmio_ops);
    return res;
}

static int ath10k_init_msi(PCIDevice *pdev) {
	//ATH10KState *d = ATH10K(pdev);
	Error *local_err = NULL;
	int res = msi_init(pdev, 0, 32, true, true, &local_err);
    if (local_err) {
        hw_error("failed to init msi");
    }
    return res;
}

static void pci_ath10k_realize(PCIDevice *pci_dev, Error **errp) {
	printf("Entering pci_ath10k_realize\n");
	//DeviceState *dev = DEVICE(pci_dev);
	ATH10KState *d = ATH10K(pci_dev);
	qemu_macaddr_default_if_unset(&d->conf.macaddr);

    memory_region_init_io(&d->mmio, OBJECT(d), &ath10k_mmio_ops, d,
                          "ath10k-mmio", 0x10000000);
    pci_register_bar(pci_dev, 0, PCI_BASE_ADDRESS_SPACE_MEMORY, &d->mmio);

	memory_region_init(&d->msix, OBJECT(d), "ath10k-msix",
                       0x1000000);
    pci_register_bar(pci_dev, 1, PCI_BASE_ADDRESS_SPACE_MEMORY, &d->msix);

	if (ath10k_add_pm_capability(pci_dev) < 0) {
		hw_error("Failed to initialize PM capability");
	}

	if (ath10k_init_msi(pci_dev) < 0) {
		hw_error("Failed to initialize MSI");
	}

	printf("Leaving pci_ath10k_realize\n");
}

static void ath10k_instance_init(Object *obj) {
	printf("Entering ath10k_instance_init\n");
	ATH10KState *n = ATH10K(obj);
	device_add_bootindex_property(obj, &n->conf.bootindex,
					"bootindex", "ethernet-phy@0",
					DEVICE(n), NULL);
	printf("Leavin ath10k_instance_init\n");
}

static const TypeInfo ath10k_info = {
	.name          = "ath10k",
	.parent        = TYPE_PCI_DEVICE,
	.instance_size = sizeof(ATH10KState),
	.instance_init = ath10k_instance_init,
	.class_size    = sizeof(ATH10KClass),
	.abstract      = false,
	.class_init    = ath10k_class_init,
	.instance_init = ath10k_instance_init,
	.interfaces = (InterfaceInfo[]) {
		{ INTERFACE_CONVENTIONAL_PCI_DEVICE },
		{ },
	},
};

static void ath10k_register_types(void) {
	printf("Entering ath10k_register_types\n");
	type_register_static(&ath10k_info);
	printf("Leaving ath10k_register_types\n");
}

type_init(ath10k_register_types)
