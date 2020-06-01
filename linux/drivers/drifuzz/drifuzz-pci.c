#include <linux/init.h>
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/fs.h>
#include <linux/ioport.h>       
#include <linux/pci.h>
#include <linux/delay.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Zekun Shen");
MODULE_DESCRIPTION("A command channel between linux guest and qemu host");
MODULE_VERSION("0.01");

#define qemu_driver_name "Qemu driver"

static int device_open_count = 0;
static int major_num;
#define CMD_ADDR 0x8
#define CMD_ARG1 0x10
#define CMD_ARG2 0x18
#define CMD_ARG3 0x20
#define ACT 0x1

/* shared */
enum ACTIONS {
	CONST_DMA_INIT = 1,
	CONST_DMA_EXIT,
	STREAM_DMA_INIT,
	STREAM_DMA_EXIT,
    EXEC_INIT,
    EXEC_EXIT,
    SUBMIT_STAGE,
	SUBMIT_KCOV_TRACE,
	KASAN,
	REQ_RESET,
};

struct qemu_adapter {
	void* hw_addr;
	struct pci_dev *pdev;
};

static struct qemu_adapter *adapter = NULL;

/* Handler */
void handle_const_dma_init(uint64_t dma_addr, uint64_t addr, uint64_t size) {
	if (adapter) {
		//printk(KERN_INFO "Get dma_init\n");
		writeq(CONST_DMA_INIT, adapter->hw_addr + CMD_ADDR);
		writeq(dma_addr, adapter->hw_addr + CMD_ARG1);
		writeq(addr, adapter->hw_addr + CMD_ARG2);
		writeq(size, adapter->hw_addr + CMD_ARG3);
		writeq(ACT, adapter->hw_addr);
	}
	else {
		//printk(KERN_INFO "Get dma_init: adapter not ready\n");
	}
}
EXPORT_SYMBOL(handle_const_dma_init);

void handle_const_dma_exit(uint64_t dma_addr) {
	if (adapter) {
		// printk(KERN_INFO "Get dma_exit\n");
		writeq(CONST_DMA_EXIT, adapter->hw_addr + CMD_ADDR);
		writeq(dma_addr, adapter->hw_addr + CMD_ARG1);
		writeq(ACT, adapter->hw_addr);
	}
}
EXPORT_SYMBOL(handle_const_dma_exit);
void handle_stream_dma_init(uint64_t dma_addr, uint64_t addr, uint64_t size) {
	if (adapter) {
		//printk(KERN_INFO "Get dma_init\n");
		writeq(STREAM_DMA_INIT, adapter->hw_addr + CMD_ADDR);
		writeq(dma_addr, adapter->hw_addr + CMD_ARG1);
		writeq(addr, adapter->hw_addr + CMD_ARG2);
		writeq(size, adapter->hw_addr + CMD_ARG3);
		writeq(ACT, adapter->hw_addr);
	}
	else {
		//printk(KERN_INFO "Get dma_init: adapter not ready\n");
	}
}
EXPORT_SYMBOL(handle_stream_dma_init);

void handle_stream_dma_exit(uint64_t dma_addr) {
	if (adapter) {
		// printk(KERN_INFO "Get dma_exit\n");
		writeq(STREAM_DMA_EXIT, adapter->hw_addr + CMD_ADDR);
		writeq(dma_addr, adapter->hw_addr + CMD_ARG1);
		writeq(ACT, adapter->hw_addr);
	}
}
EXPORT_SYMBOL(handle_stream_dma_exit);

static void handle_exec_init(void) {
    if (adapter) {
        writeq(EXEC_INIT, adapter->hw_addr + CMD_ADDR);
		writeq(ACT, adapter->hw_addr);
    }
}
static void handle_exec_exit(void) {
    if (adapter) {
        writeq(EXEC_EXIT, adapter->hw_addr + CMD_ADDR);
		writeq(ACT, adapter->hw_addr);
    }
}
static void handle_submit_stage(uint64_t stage) {
    if (adapter) {
        writeq(SUBMIT_STAGE, adapter->hw_addr + CMD_ADDR);
        writeq(stage, adapter->hw_addr + CMD_ARG1);
		writeq(ACT, adapter->hw_addr);
    }
}
void handle_submit_kcov_trace(uint64_t address, uint64_t size) {
    if (adapter) {
        writeq(SUBMIT_KCOV_TRACE, adapter->hw_addr + CMD_ADDR);
        writeq(virt_to_phys(address), adapter->hw_addr + CMD_ARG1);
		writeq(size, adapter->hw_addr + CMD_ARG2);
		writeq(ACT, adapter->hw_addr);
    }
}
EXPORT_SYMBOL(handle_submit_kcov_trace);

void handle_kasan(void) {
	printk(KERN_INFO "handle_kasan\n");
	if (adapter) {
        writeq(KASAN, adapter->hw_addr + CMD_ADDR);
		writeq(ACT, adapter->hw_addr);
	}
}
EXPORT_SYMBOL(handle_kasan);

void handle_req_reset(void) {
	printk(KERN_INFO "handle_reset\n");
	if (adapter) {
        writeq(REQ_RESET, adapter->hw_addr + CMD_ADDR);
		writeq(ACT, adapter->hw_addr);
	}
}

static int handle_command(void* buffer, size_t len) {
	uint64_t *pbuffer;
	uint64_t cmd;
	uint64_t *argv;
	int argc;
	size_t nread = 0;
	pbuffer = (uint64_t *)buffer;
	if (len == 0 || len % 8) {
		return -EINVAL;
	}
	
	cmd = *pbuffer;
	nread += 8;
	argv = pbuffer + 1;
	argc = (len - 8) / 8;
	switch (cmd)
	{
	case CONST_DMA_INIT:
		WARN_ON(len != 0x20);
		handle_const_dma_init(argv[0], argv[1], argv[2]);
		return 0x20;
	case CONST_DMA_EXIT:
		WARN_ON(len != 0x10);
		handle_const_dma_exit(argv[0]);
		return 0x10;
	case STREAM_DMA_INIT:
		WARN_ON(len != 0x20);
		handle_stream_dma_init(argv[0], argv[1], argv[2]);
		return 0x20;
	case STREAM_DMA_EXIT:
		WARN_ON(len != 0x10);
		handle_stream_dma_exit(argv[0]);
		return 0x10;
    case EXEC_INIT:
        WARN_ON(len!= 0x8);
        handle_exec_init();
        return 0x8;
    case EXEC_EXIT:
        WARN_ON(len!= 0x8);
        handle_exec_exit();
        return 0x8;
    case SUBMIT_STAGE:
        WARN_ON(len!= 0x10);
        handle_submit_stage(argv[0]);
        return 0x10;
	case SUBMIT_KCOV_TRACE:
		WARN_ON(len!= 0x18);
		handle_submit_kcov_trace(argv[0], argv[1]);
		return 0x18;
	case REQ_RESET:
		WARN_ON(len != 0x8);
		handle_req_reset();
	default:
		printk(KERN_INFO "Unknow action\n");
		return 0x4;
	}
	return 0;
}

/* File ops */
static ssize_t device_write(struct file *flip, const char *buffer, size_t len,
		loff_t *offset) {
	//uint64_t *p = (uint64_t*) buffer;
	int num = 0;
	void *kbuf = kmalloc(len, GFP_KERNEL);
	if (copy_from_user(kbuf, buffer, len)) {
		return -EIO;
	}
	if ((num = handle_command(kbuf, len)) == 0) {
		return -EINVAL;
	}
	return num;
	
}

static ssize_t device_read(struct file *flip, char *buffer, size_t len, 
		loff_t *offset) {
	printk(KERN_ALERT "This operation is not supported.\n");
	return -EINVAL;
}

static int device_open(struct inode *inode, struct file *file) {
	if (device_open_count) {
		return -EBUSY;
	}
	device_open_count++;
	try_module_get(THIS_MODULE);
	return 0;
}

static int device_release(struct inode *inode, struct file *file) {
	device_open_count--;
	module_put(THIS_MODULE);
	return 0;
}

static struct file_operations file_ops = {
	.read = device_read,
	.write = device_write,
	.open = device_open,
	.release = device_release
};

/* File ops end */

/* PCI */
static int qemu_probe(struct pci_dev *pdev, const struct pci_device_id *ent) {
	printk(KERN_INFO "Qemu probe\n Hello!\n");
	int err;
	dma_addr_t dma_handle;
	void *const_dma_region;
	void *stream_dma_region;
	// int bars;
	//bars = pci_select_bars(pdev, IORESOURCE_MEM | IORESOURCE_IO);
	if ((err = pci_enable_device(pdev)))
		return err;

	// if ((err = pci_request_selected_regions(pdev, bars, qemu_driver_name)))
	// 	goto somewhere1;
	
	// pci_set_master(pdev);
	// if ((err = pci_save_state(pdev))) {
	// 	goto somewhere2;
	// }
	adapter = kmalloc(sizeof(struct qemu_adapter), GFP_KERNEL);
	adapter->pdev = pdev;
	adapter->hw_addr = pci_ioremap_bar(pdev, 0);
	pci_set_drvdata(pdev, adapter);


	const_dma_region =
			dma_alloc_coherent(&pdev->dev, 0x1000, &dma_handle, GFP_KERNEL);

	*(char*)const_dma_region = 'A';
	*((char*)const_dma_region + 0x111) = 'A';
	dma_free_coherent(&pdev->dev, 0x1000, const_dma_region, dma_handle);


	stream_dma_region = kmalloc(0x101, GFP_KERNEL);
	*((char*)stream_dma_region + 0x100) = '\x00';
	dma_handle = dma_map_single(&pdev->dev, stream_dma_region, 0x100, DMA_FROM_DEVICE);

	if (dma_mapping_error(&pdev->dev, dma_handle)) {
		pr_info("dma_map_single() failed\n");
	} else {
		pr_info("dma_map_single() succeeded");
	}
	dma_unmap_single(&pdev->dev, dma_handle, 0x100, DMA_FROM_DEVICE);
	// udelay(100);
	printk(KERN_INFO "stream dma data: %s\n", (char*)stream_dma_region);
	kfree(stream_dma_region);
	return 0;
}

static void qemu_remove(struct pci_dev *pdev) {
	//pci_release_selected_regions(pdev, bars);
	kfree(pci_get_drvdata(pdev));
	pci_disable_device(pdev);
}

static const struct pci_device_id qemu_pci_tbl[] = {
	{PCI_DEVICE(0x7777, 0x7777)},
	{}
};
static struct pci_driver qemu_driver = {
	.name 		= qemu_driver_name,
	.id_table 	= qemu_pci_tbl,
	.probe 		= qemu_probe,
	.remove 	= qemu_remove,
};

/* PCI ends */

/* Module */
int __init qemu_init_module(void) {
	int ret;
	printk(KERN_INFO "Qemu init\n Hello!\n");
	if ((ret = pci_register_driver(&qemu_driver)) != 0) {
		printk(KERN_ALERT "Could not register pci: %d\b", ret);
		return ret;
	}
	major_num = register_chrdev(0, qemu_driver_name, &file_ops);
	if (major_num < 0) {
		printk(KERN_ALERT "Could not register device: %d\n", major_num);
		return major_num;
	} else {
		printk(KERN_INFO "Qemu module loaded with major %d\n", major_num);
		return 0;
	}
}
module_init(qemu_init_module);

void __exit qemu_exit_module(void) {
	unregister_chrdev(major_num, qemu_driver_name);
	printk(KERN_INFO "Qemu exit\n Goodbye!\n");
}

module_exit(qemu_exit_module);
/* Module ends */
